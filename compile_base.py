#!/usr/bin/env python
# This Python file uses the following encoding: utf-8

import argparse
import operator
import os
import re
import shutil
from subprocess import call

# Variables
global_version = '0.203.0'
protoc_executable = "protoc"
package_name = 'POGOProtos.Rpc'
input_file = "POGOProtos.Rpc.proto"
base_file = os.path.abspath("base/base.proto")
protos_path = os.path.abspath("base")
gen_last_files = os.path.abspath("base/last_files")


def is_blank(my_string):
    if my_string and my_string.strip():
        return False
    return True


# args
parser = argparse.ArgumentParser()
parser.add_argument("-gm", "--generate_game_master", help="Generates v2_GAME_MASTER.txt.")
parser.add_argument("-ga", "--generate_asset_digest", help="Generates ASSET_DIGEST.txt.")
parser.add_argument("-l", "--lang", help="Language to produce proto single file.")
parser.add_argument("-v", "--version", help="Set version out ex:. (0.195.2)")
parser.add_argument("-o", "--out_path", help="Output path for proto single file.")
parser.add_argument("-m", "--java_multiple_files", action='store_true',
                    help='Write each message to a separate .java file.')
parser.add_argument("-g", "--generate_only", action='store_true', help='Generates only proto compilable.')
parser.add_argument("-b", "--generate_new_base", action='store_true', help='Generates new proto base refs.')
parser.add_argument("-k", "--keep_proto_file", action='store_true', help='Do not remove .proto file after compiling.')
parser.add_argument("-gf", "--generate_proto_files", action='store_true', help='Generates base/last_files/*.proto.')
parser.add_argument("-ch", "--clean_holo_string", action='store_true',
                    help='Remove holo* from names out HoloPokemonId -> PokemonId.')
args = parser.parse_args()

# Set defaults args
lang = args.lang or "proto"
out_path = args.out_path or "out/single_file/" + lang
java_multiple_files = args.java_multiple_files
gen_only = args.generate_only
gen_files = args.generate_proto_files
version = args.version or global_version
gen_base = args.generate_new_base
keep_file = args.keep_proto_file
clean_holo_string = args.clean_holo_string
gen_game_master = args.generate_game_master or None
gen_asset_digest = args.generate_asset_digest or None

# Determine where path's and variables
raw_name = "v" + version + ".proto"
raw_proto_file = os.path.abspath("base/" + raw_name)
out_path = os.path.abspath(out_path)

if gen_asset_digest is not None:
    if not os.path.exists(gen_asset_digest):
        print("Binary not found.")
        exit(0)
    commands = []
    print("Try to decode " + gen_asset_digest + ".txt....")
    pogo_protos_path = './base'
    pogo_protos_target = 'POGOProtos.Rpc.AssetDigestOutProto'
    pogo_protos_template = './base/' + raw_name

    commands.append(
        """"{0}" --proto_path="{1}" --decode "{2}" {3} <{4}> {5}""".format(
            protoc_executable,
            pogo_protos_path,
            pogo_protos_target,
            pogo_protos_template,
            gen_asset_digest,
            gen_asset_digest + '.txt'
        ))

    for command in commands:
        call(command, shell=True)

    exit(0);

if gen_game_master is not None:
    if not os.path.exists(gen_game_master):
        print("Binary not found.")
        exit(0)
    commands = []
    print("Try to decode " + gen_game_master + ".txt....")
    pogo_protos_path = './base'
    pogo_protos_target = 'POGOProtos.Rpc.DownloadGmTemplatesResponseProto'
    pogo_protos_template = './base/' + raw_name

    commands.append(
        """"{0}" --proto_path="{1}" --decode "{2}" {3} <{4}> {5}""".format(
            protoc_executable,
            pogo_protos_path,
            pogo_protos_target,
            pogo_protos_template,
            gen_game_master,
            gen_game_master + '.txt'
        ))

    for command in commands:
        call(command, shell=True)

    exit(0);

# Add licenses
head = '/*\n'
head += '* Copyright 2016-2021 --=FurtiF=--.\n'
head += '*\n'
head += '* Licensed under the\n'
head += '*	Educational Community License, Version 2.0 (the "License"); you may\n'
head += '*	not use this file except in compliance with the License. You may\n'
head += '*	obtain a copy of the License at\n'
head += '*\n'
head += '*	http://www.osedu.org/licenses/ECL-2.0\n'
head += '*\n'
head += '*	Unless required by applicable law or agreed to in writing,\n'
head += '*	software distributed under the License is distributed on an "AS IS"\n'
head += '*	BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express\n'
head += '*	or implied. See the License for the specific language governing\n'
head += '*	permissions and limitations under the License.\n'
head += '*\n* Version: ' + version + '\n*\n'
head += '*/\n\n'
head += 'syntax = "proto3";\n'
head += 'package %s;\n\n' % package_name

## Load Base
base_enums = {}
base_messages = {}
base_as_data = False
base_is_enum = False
base_proto_name = ''
base_data = ''

with open(base_file, 'r') as proto_file:
    for proto_line in proto_file.readlines():
        if proto_line.startswith("enum") or proto_line.startswith("message"):
            base_as_data = True
            base_proto_name = proto_line.split(" ")[1]
        if proto_line.startswith("enum"):
            base_is_enum = True
        if proto_line.startswith("message"):
            base_is_enum = False
        if proto_line.startswith("}"):
            base_data += proto_line
            if base_is_enum:
                base_enums.setdefault(base_proto_name, base_data)
            else:
                base_messages.setdefault(base_proto_name, base_data)
            base_as_data = False
            base_is_enum = False
            base_proto_name = ''
            base_data = ''
        if base_as_data:
            base_data += proto_line

try:
    os.remove(base_file)
except OSError:
    pass

open_for_new = open(base_file, 'a')
new_base_file = head

# Re-order base
for p in sorted(base_enums):
    new_base_file += base_enums[p] + "\n"
for p in sorted(base_messages):
    new_base_file += base_messages[p] + "\n"

open_for_new.writelines(new_base_file[:-1])
open_for_new.close()

# Clean up previous out
try:
    os.remove(out_path)
except OSError:
    pass

if out_path and os.path.exists(out_path):
    shutil.rmtree(out_path)

# Create necessary directory
if not os.path.exists(out_path):
    os.makedirs(out_path)

commands = []


def finish_compile(out_path, lang):
    if lang == 'python':
        pogo_protos_path = os.path.join(out_path, "POGOProtos")

        for root, dirnames, filenames in os.walk(pogo_protos_path):
            init_path = os.path.join(root, '__init__.py')

            with open(init_path, 'w') as init_file:
                if pogo_protos_path is root:
                    init_file.write(
                        "'Generated'; import os; import sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))")


def open_proto_file(main_file, head):
    new_proto_single_file = main_file.replace(raw_name, input_file)

    if os.path.exists(new_proto_single_file):
        os.unlink(new_proto_single_file)

    open_for_new = open(new_proto_single_file, 'a')

    if not gen_only:
        # Add options by language
        if java_multiple_files and lang == "java":
            head += 'option java_multiple_files = true;\n\n'
        elif lang == "cpp":
            head += 'option optimize_for = CODE_SIZE;\n\n'

    open_for_new.writelines(head)

    messages = ''
    # ignored_one_of = {}
    # is_ignored = False
    proto_name = ''

    with open(main_file, 'r') as proto_file:
        for proto_line in proto_file.readlines():
            # if is_ignored and operator.contains(proto_line, "//}"):
            #     is_ignored = False
            # if operator.contains(proto_line, "//ignored_"):
            #     proto_line = proto_line.replace("//ignored_", "//")
            #     is_ignored = True
            # if is_ignored and operator.contains(proto_line, "=") and not operator.contains(proto_line, "//none = 0;"):
            #     ignored_one_of.setdefault(proto_line.strip().split("=")[1], proto_line.strip().split("=")[0].strip())
            if proto_line.startswith("syntax"):
                continue
            if proto_line.startswith("package"):
                continue
            # Ignore file licenses
            if proto_line.startswith("/*"):
                continue
            if proto_line.startswith("*"):
                continue
            if proto_line.startswith("*/"):
                continue
            # ---
            if is_blank(proto_line):
                continue
            if operator.contains(proto_line, "message ") or operator.contains(proto_line, "enum ") or operator.contains(
                    proto_line, "oneof ") and operator.contains(
                proto_line, "{"):
                proto_name = proto_line.split(" ")[1].strip()
            elif proto_name == "HoloPokemonId" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "HOLO_POKEMON_ID_"):
                proto_line = proto_line.replace("HOLO_POKEMON_ID_", "").replace("POKEMON_UNSET",
                                                                                "V0000_POKEMON_MISSINGNO")
                proto_line = proto_line.replace(proto_line.split("_POKEMON_")[0].strip(), "").replace("_POKEMON_", "")
                if operator.contains(proto_line, "NIDORAN") and operator.contains(proto_line, "= 29;"):
                    proto_line = proto_line.replace("NIDORAN", "NIDORAN_FEMALE")
                elif operator.contains(proto_line, "NIDORAN") and operator.contains(proto_line, "= 32;"):
                    proto_line = proto_line.replace("NIDORAN", "NIDORAN_MALE")
            elif proto_name == "HoloPokemonFamilyId" and not operator.contains(proto_line,
                                                                               "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "HOLO_POKEMON_FAMILY_ID_"):
                proto_line = proto_line.replace("HOLO_POKEMON_FAMILY_ID_", "").replace("FAMILY_UNSET",
                                                                                       "V0000_FAMILY_UNSET")
                proto_line = proto_line.replace(proto_line.split("_FAMILY_")[0].strip(), "").replace("_FAMILY_",
                                                                                                     "FAMILY_")
                if operator.contains(proto_line, "NIDORAN") and operator.contains(proto_line, "= 29;"):
                    proto_line = proto_line.replace("NIDORAN", "NIDORAN_FEMALE")
                elif operator.contains(proto_line, "NIDORAN") and operator.contains(proto_line, "= 32;"):
                    proto_line = proto_line.replace("NIDORAN", "NIDORAN_MALE")
            elif proto_name == "HoloBadgeType" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "HOLO_BADGE_TYPE_"):
                proto_line = proto_line.replace("HOLO_BADGE_TYPE_", "")
            elif proto_name == "BattleHubSection" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "BATTLE_HUB_SECTION_"):
                proto_line = proto_line.replace("BATTLE_HUB_SECTION_", "")
            elif proto_name == "HoloPokemonMove" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "HOLO_POKEMON_MOVE_"):
                proto_line = proto_line.replace("HOLO_POKEMON_MOVE_", "").replace("MOVE_UNSET",
                                                                                  "V0000_MOVE_UNSET")
                proto_line = proto_line.replace(proto_line.split("_MOVE_")[0].strip(), "").replace("_MOVE_",
                                                                                                   "").replace("UNSET",
                                                                                                               "MOVE_UNSET")
            elif proto_name == "AdFeedbackLikeReason" and not operator.contains(proto_line,
                                                                                "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line,
                                                       "AD_FEEDBACK_LIKE_REASON_AD_FEEDBACK_LIKE_REASON_"):
                proto_line = proto_line.replace("AD_FEEDBACK_LIKE_REASON_AD_FEEDBACK_LIKE_REASON_",
                                                "AD_FEEDBACK_LIKE_REASON_")
            elif proto_name == "AdFeedbackComplaintReason" and not operator.contains(proto_line,
                                                                                     "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line,
                                                       "AD_FEEDBACK_COMPLAINT_REASON_AD_FEEDBACK_COMPLAINT_REASON_"):
                proto_line = proto_line.replace("AD_FEEDBACK_COMPLAINT_REASON_AD_FEEDBACK_COMPLAINT_REASON_",
                                                "AD_FEEDBACK_COMPLAINT_REASON_")
            elif proto_name == "AdFeedbackNotInterestedReason" and not operator.contains(proto_line,
                                                                                         "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line,
                                                       "AD_FEEDBACK_NOT_INTERESTED_REASON_AD_FEEDBACK_NOT_INTERESTED_REASON_"):
                proto_line = proto_line.replace("AD_FEEDBACK_NOT_INTERESTED_REASON_AD_FEEDBACK_NOT_INTERESTED_REASON_",
                                                "AD_FEEDBACK_NOT_INTERESTED_REASON_")
            elif proto_name == "ArMappingEntrySource" and not operator.contains(proto_line,
                                                                                "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "TITAN_"):
                proto_line = proto_line.replace("TITAN_", "")
            elif proto_name == "ArMappingTutorialPage" and not operator.contains(proto_line,
                                                                                 "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "TITAN_"):
                proto_line = proto_line.replace("TITAN_", "")
            elif proto_name == "BattleHubSubsection" and not operator.contains(proto_line,
                                                                               "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "BATTLE_HUB_SUBSECTION_"):
                proto_line = proto_line.replace("BATTLE_HUB_SUBSECTION_", "")
            elif proto_name == "BuddyActivityCategory" and not operator.contains(proto_line,
                                                                                 "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "BUDDY_ACTIVITY_CATEGORY_BUDDY_CATEGORY_"):
                proto_line = proto_line.replace("BUDDY_ACTIVITY_CATEGORY_BUDDY_CATEGORY_", "BUDDY_CATEGORY_")
            elif proto_name == "BuddyActivity" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "BUDDY_ACTIVITY_BUDDY_ACTIVITY_"):
                proto_line = proto_line.replace("BUDDY_ACTIVITY_BUDDY_ACTIVITY_", "BUDDY_ACTIVITY_")
            elif proto_name == "BuddyAnimation" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "BUDDY_ANIMATION_BUDDY_ANIMATION_"):
                proto_line = proto_line.replace("BUDDY_ANIMATION_BUDDY_ANIMATION_", "BUDDY_ANIMATION_")
            elif proto_name == "BuddyEmotionLevel" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "BUDDY_EMOTION_LEVEL_BUDDY_EMOTION_LEVEL_"):
                proto_line = proto_line.replace("BUDDY_EMOTION_LEVEL_BUDDY_EMOTION_LEVEL_", "BUDDY_EMOTION_LEVEL_")
            elif proto_name == "BuddyLevel" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "BUDDY_LEVEL_BUDDY_LEVEL_"):
                proto_line = proto_line.replace("BUDDY_LEVEL_BUDDY_LEVEL_", "BUDDY_LEVEL_")
            elif proto_name == "CameraInterpolation" and not operator.contains(proto_line,
                                                                               "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "CAMERA_INTERPOLATION_"):
                proto_line = proto_line.replace("CAMERA_INTERPOLATION_", "")
            elif proto_name == "CameraTarget" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "CAMERA_TARGET_"):
                proto_line = proto_line.replace("CAMERA_TARGET_", "")
            elif proto_name == "CombatType" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "COMBAT_TYPE_COMBAT_TYPE_"):
                proto_line = proto_line.replace("COMBAT_TYPE_COMBAT_TYPE_", "COMBAT_TYPE_")
            elif proto_name == "EggIncubatorType" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "EGG_INCUBATOR_TYPE_"):
                proto_line = proto_line.replace("EGG_INCUBATOR_TYPE_", "")
            elif proto_name == "EggSlotType" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "EGG_SLOT_TYPE_"):
                proto_line = proto_line.replace("EGG_SLOT_TYPE_", "")
            elif proto_name == "FeatureKind" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "PLATFORM_"):
                proto_line = proto_line.replace("PLATFORM_", "")
            elif proto_name == "FeatureType" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "PLATFORM_"):
                proto_line = proto_line.replace("PLATFORM_", "")
            elif proto_name == "FortType" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "FORT_TYPE_"):
                proto_line = proto_line.replace("FORT_TYPE_", "")
            elif proto_name == "GameChatActions" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "PLATFORM_"):
                proto_line = proto_line.replace("PLATFORM_", "")
            elif proto_name == "GuiTransitionType" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "PLATFORM_"):
                proto_line = proto_line.replace("PLATFORM_", "")
            elif proto_name == "GymBadgeType" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "GYM_BADGE_TYPE_GYM_BADGE_"):
                proto_line = proto_line.replace("GYM_BADGE_TYPE_GYM_BADGE_", "GYM_BADGE_")
            elif proto_name == "HoloActivityType" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "HOLO_ACTIVITY_TYPE_"):
                proto_line = proto_line.replace("HOLO_ACTIVITY_TYPE_", "")
            elif proto_name == "HoloItemCategory" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "HOLO_ITEM_CATEGORY_"):
                proto_line = proto_line.replace("HOLO_ITEM_CATEGORY_", "")
            elif proto_name == "HoloIapItemCategory" and not operator.contains(proto_line,
                                                                               "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "HOLO_IAP_ITEM_CATEGORY_"):
                proto_line = proto_line.replace("HOLO_IAP_ITEM_CATEGORY_", "")
            elif proto_name == "HoloItemEffect" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "HOLO_ITEM_EFFECT_"):
                proto_line = proto_line.replace("HOLO_ITEM_EFFECT_", "")
            elif proto_name == "HoloItemEffect" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "HOLO_ITEM_EFFECT_"):
                proto_line = proto_line.replace("HOLO_ITEM_EFFECT_", "")
            elif proto_name == "HoloItemType" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "HOLO_ITEM_TYPE_"):
                proto_line = proto_line.replace("HOLO_ITEM_TYPE_", "")
            elif proto_name == "FriendshipLevelMilestone" and not operator.contains(proto_line,
                                                                                    "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "FRIENDSHIP_LEVEL_MILESTONE_FRIENDSHIP_LEVEL_"):
                proto_line = proto_line.replace("FRIENDSHIP_LEVEL_MILESTONE_FRIENDSHIP_LEVEL_", "FRIENDSHIP_LEVEL_")
            elif proto_name == "HoloPokemonClass" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "HOLO_POKEMON_CLASS_"):
                proto_line = proto_line.replace("HOLO_POKEMON_CLASS_", "")
            elif proto_name == "HoloPokemonEggType" and not operator.contains(proto_line,
                                                                              "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "HOLO_POKEMON_EGG_TYPE_"):
                proto_line = proto_line.replace("HOLO_POKEMON_EGG_TYPE_", "")
            elif proto_name == "HoloPokemonMovementType" and not operator.contains(proto_line,
                                                                                   "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "HOLO_POKEMON_MOVEMENT_TYPE_POKEMON_ENC_"):
                proto_line = proto_line.replace("HOLO_POKEMON_MOVEMENT_TYPE_POKEMON_ENC_", "")
            elif proto_name == "HoloPokemonNature" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "HOLO_POKEMON_NATURE_"):
                proto_line = proto_line.replace("HOLO_POKEMON_NATURE_", "").replace("NATURE_UNKNOWN",
                                                                                    "V0000_POKEMON_NATURE_UNKNOWN")
                proto_line = proto_line.replace(proto_line.split("_POKEMON_NATURE_")[0].strip(), "").replace(
                    "_POKEMON_", "POKEMON_")
            elif proto_name == "HoloPokemonType" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "HOLO_POKEMON_TYPE_"):
                proto_line = proto_line.replace("HOLO_POKEMON_TYPE_", "")
            elif proto_name == "HoloTemporaryEvolutionId" and not operator.contains(proto_line,
                                                                                    "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "HOLO_TEMPORARY_EVOLUTION_ID_"):
                proto_line = proto_line.replace("HOLO_TEMPORARY_EVOLUTION_ID_", "")
            elif proto_name == "IdentityProvider" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "PLATFORM_"):
                proto_line = proto_line.replace("PLATFORM_", "")
            elif proto_name == "InventoryUpgradeType" and not operator.contains(proto_line,
                                                                                "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "INVENTORY_UPGRADE_TYPE_"):
                proto_line = proto_line.replace("INVENTORY_UPGRADE_TYPE_", "")
            elif proto_name == "InvitationType" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "PLATFORM_INVITATION_TYPE_INVITATION_TYPE_"):
                proto_line = proto_line.replace("PLATFORM_INVITATION_TYPE_INVITATION_TYPE_", "INVITATION_TYPE_")
            elif proto_name == "Item" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "ITEM_ITEM_"):
                if operator.contains(proto_line, "ITEM_ITEM_ITEM_STORAGE_UPGRADE"):
                    proto_line = proto_line.replace("ITEM_ITEM_ITEM_STORAGE_UPGRADE", "ITEM_ITEM_STORAGE_UPGRADE")
                elif not operator.contains(proto_line, "ITEM_ITEM_STORAGE_UPGRADE"):
                    proto_line = proto_line.replace("ITEM_ITEM_", "ITEM_")
            elif proto_name == "MapLayer" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "PLATFORM_"):
                proto_line = proto_line.replace("PLATFORM_", "")
            elif proto_name == "Method" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "METHOD_METHOD_"):
                proto_line = proto_line.replace("METHOD_METHOD_", "METHOD_")
            elif proto_name == "NotificationCategory" and not operator.contains(proto_line,
                                                                                "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "_unset__notification_category"):
                proto_line = proto_line.replace("_unset__notification_category", "_UNSET")
            elif proto_name == "NotificationState" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "PLATFORM_"):
                proto_line = proto_line.replace("PLATFORM_", "")
            elif proto_name == "OmniNotificationSubscriptionType" and not operator.contains(proto_line,
                                                                                            "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "PLATFORM_"):
                proto_line = proto_line.replace("PLATFORM_", "")
            elif proto_name == "OnboardingType" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "PLATFORM_"):
                proto_line = proto_line.replace("PLATFORM_", "")
            elif proto_name == "POIDecorationFollowFlags" and not operator.contains(proto_line,
                                                                                    "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line,
                                                       "POI_DECORATION_FOLLOW_FLAGS_POIDECORATIONFOLLOWFLAGS_AUTO_INVALID"):
                proto_line = proto_line.replace("POI_DECORATION_FOLLOW_FLAGS_POIDECORATIONFOLLOWFLAGS_AUTO_INVALID",
                                                "POI_DECORATION_FOLLOW_FLAGS_UNSET")
            elif proto_name == "Platform" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "PLATFORM_PLATFORM_"):
                proto_line = proto_line.replace("PLATFORM_PLATFORM_", "PLATFORM_")
            elif proto_name == "PlatformClientAction" and not operator.contains(proto_line,
                                                                                "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "PLATFORM_PLATFORM_"):
                proto_line = proto_line.replace("PLATFORM_PLATFORM_", "")
            elif proto_name == "PlayerAvatarType" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "PLAYER_AVATAR_TYPE_"):
                proto_line = proto_line.replace("PLAYER_AVATAR_TYPE_", "")
            elif proto_name == "PlayerSubmissionAction" and not operator.contains(proto_line,
                                                                                  "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "TITAN_"):
                proto_line = proto_line.replace("TITAN_", "")
            elif proto_name == "PlayerSubmissionTypeProto" and not operator.contains(proto_line,
                                                                                     "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "PLATFORM_"):
                proto_line = proto_line.replace("PLATFORM_", "")
            elif proto_name == "PoiEditImageEntrySource" and not operator.contains(proto_line,
                                                                                   "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "TITAN_"):
                proto_line = proto_line.replace("TITAN_", "")
            elif proto_name == "PoiImageType" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "PLATFORM_"):
                proto_line = proto_line.replace("PLATFORM_", "")
            elif proto_name == "PoiInvalidReason" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "PLATFORM_"):
                proto_line = proto_line.replace("PLATFORM_", "")
            elif proto_name == "PokemonBadge" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "POKEMON_BADGE_POKEMON_BADGE_"):
                proto_line = proto_line.replace("POKEMON_BADGE_POKEMON_BADGE_", "POKEMON_BADGE_")
            elif proto_name == "PokemonCreateContext" and not operator.contains(proto_line,
                                                                                "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "POKEMON_CREATE_CONTEXT_"):
                proto_line = proto_line.replace("POKEMON_CREATE_CONTEXT_", "")
            elif proto_name == "PokemonTagColor" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "POKEMON_TAG_COLOR_POKEMON_TAG_COLOR_"):
                proto_line = proto_line.replace("POKEMON_TAG_COLOR_POKEMON_TAG_COLOR_", "POKEMON_TAG_COLOR_")
            elif proto_name == "ProviderType" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "PLATFORM_"):
                proto_line = proto_line.replace("PLATFORM_", "")
            elif proto_name == "QuestType" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "QUEST_TYPE_"):
                proto_line = proto_line.replace("QUEST_TYPE_", "")
            elif proto_name == "RaidLevel" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "RAID_LEVEL_RAID_LEVEL_"):
                proto_line = proto_line.replace("RAID_LEVEL_RAID_LEVEL_", "RAID_LEVEL_")
            elif proto_name == "SouvenirTypeId" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "SOUVENIR_TYPE_ID_"):
                proto_line = proto_line.replace("SOUVENIR_TYPE_ID_", "")
            elif proto_name == "SponsorPoiInvalidReason" and not operator.contains(proto_line,
                                                                                   "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "PLATFORM_"):
                proto_line = proto_line.replace("PLATFORM_", "")
            elif proto_name == "Store" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "STORE_STORE_"):
                proto_line = proto_line.replace("STORE_STORE_", "STORE_")
            elif proto_name == "Team" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "TEAM_TEAM_"):
                proto_line = proto_line.replace("TEAM_TEAM_", "TEAM_")
            elif proto_name == "TutorialCompletion" and not operator.contains(proto_line,
                                                                              "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "TUTORIAL_COMPLETION_"):
                proto_line = proto_line.replace("TUTORIAL_COMPLETION_", "")
            elif proto_name == "VariableName" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "unset__variable_name"):
                proto_line = proto_line.replace("unset__variable_name", "UNSET")
            elif proto_name == "SubscriptionState" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "PLATFORM_"):
                proto_line = proto_line.replace("PLATFORM_", "")
            elif proto_name == "PokemonAlignment" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "ALIGNMENT_UNSET "):
                proto_line = proto_line.replace("POKEMON_ALIGNMENT_ALIGNMENT_UNSET", "POKEMON_ALIGNMENT_UNSET")
            elif proto_name == "PokemonGender" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "GENDER_UNSET "):
                proto_line = proto_line.replace("POKEMON_GENDER_GENDER_UNSET", "POKEMON_GENDER_UNSET")
            elif proto_name == "GameChatActions" and not operator.contains(proto_line, "{") and not operator.contains(
                    proto_line, "}") and operator.contains(proto_line, "GAME_CHAT_ACTIONS_"):
                proto_line = proto_line.replace("GAME_CHAT_ACTIONS_", "")
            elif proto_name == "HoloholoClientTelemetryIds" and not operator.contains(proto_line,
                                                                                      "{") and not operator.contains(
                proto_line, "}") and operator.contains(proto_line, "HOLOHOLO_"):
                proto_line = proto_line.replace("HOLOHOLO_", "")

            ## Others conditions...
            if not proto_line.startswith("enum") and not proto_line.startswith("message") and operator.contains(
                    proto_line, "enum") or operator.contains(proto_line, "message"):
                check_sub_message_end = False
            if operator.contains(proto_line, "enum Platform"):
                proto_line = proto_line.replace("Platorm", "REF_PY_1")
            ##

            # ## find ingored oneof's...
            # if len(ignored_one_of) > 0 and operator.contains(proto_line,
            #                                                  "=") and not is_ignored and not operator.contains(
            #     proto_line, "//") and not is_one_off and not is_enum and check_sub_message_end:
            #     if proto_line.strip().split("=")[1] in ignored_one_of:
            #         proto_line = proto_line.replace(proto_line.strip().split("=")[0].split(" ")[1],
            #                                         ignored_one_of[proto_line.strip().split("=")[1]]).replace("//", "")
            #         try:
            #             ignored_one_of.pop(proto_line.strip().split("=")[1], None)
            #         except KeyError:
            #             pass

            ## fixes int32 team, pokemon_id and others..
            if operator.contains(proto_line, "int32 team "):
                proto_line = proto_line.replace("int32", "Team")
            elif operator.contains(proto_line, "int32 pokedex_id "):
                proto_line = proto_line.replace("int32", "HoloPokemonId")
            elif operator.contains(proto_line, "int32 pokedex_id "):
                proto_line = proto_line.replace("int32", "HoloPokemonId")
            elif operator.contains(proto_line, "int32 move1 "):
                proto_line = proto_line.replace("int32", "HoloPokemonMove")
            elif operator.contains(proto_line, "int32 move2 "):
                proto_line = proto_line.replace("int32", "HoloPokemonMove")
            elif operator.contains(proto_line, "int32 move3 "):
                proto_line = proto_line.replace("int32", "HoloPokemonMove")
            elif operator.contains(proto_line, "int32 move "):
                proto_line = proto_line.replace("int32", "HoloPokemonMove")
            elif operator.contains(proto_line, "int32 pokemon_id "):
                proto_line = proto_line.replace("int32", "HoloPokemonId")
            elif operator.contains(proto_line, "int32 display_pokedex_id "):
                proto_line = proto_line.replace("int32", "HoloPokemonId")
            elif operator.contains(proto_line, "int32 rarity "):
                proto_line = proto_line.replace("int32", "HoloPokemonClass")
            elif operator.contains(proto_line, "int32 pokemon_type_id "):
                proto_line = proto_line.replace("int32", "HoloPokemonId")
            elif operator.contains(proto_line, "int32 pokedex_entry_id "):
                proto_line = proto_line.replace("int32", "HoloPokemonId")
            elif operator.contains(proto_line, "int32 pokemon_family_id "):
                proto_line = proto_line.replace("int32", "HoloPokemonFamilyId")
            # elif operator.contains(proto_line, "int32 pokedex_entry_number "):
            #     proto_line = proto_line.replace("int32", "HoloPokemonId")
            elif operator.contains(proto_line, "int32 guard_pokemon_id "):
                proto_line = proto_line.replace("int32", "HoloPokemonId")
            elif operator.contains(proto_line, "int32 item_id "):
                proto_line = proto_line.replace("int32", "Item")
            elif operator.contains(proto_line, "int32 pokeball "):
                proto_line = proto_line.replace("int32", "Item")
            elif operator.contains(proto_line, "int32 balltype "):
                proto_line = proto_line.replace("int32", "Item")
            elif operator.contains(proto_line, "int32 severity "):
                proto_line = proto_line.replace("int32", "WeatherAlertProto.Severity")
            ## others conditions
            elif operator.contains(proto_line, "Platform "):
                proto_line = proto_line.replace("Platform", "REF_PY_1")
            ##

            messages += proto_line

            if not proto_line.startswith("}") and operator.contains(proto_line, "}"):
                messages += "\n"

            if proto_line.startswith("}"):
                messages += "\n"
                # ignored_one_of.clear()
                # proto_name = ''

    ## clean bad spaces...
    messages = messages.replace("}\n\n}", "}\n}")
    messages = messages.replace("\t\t}\n\n\t}", "\t\t}\n\t}")
    ## fixes other names...
    messages = messages.replace("Titan", "")
    messages = messages.replace("Platform", "")
    if clean_holo_string:
        messages = messages.replace("Holo", "").replace("holo", "")
    # revert ref_py_x
    messages = messages.replace("REF_PY_1", "Platform")
    ##

    ## check in messages basic obfuscated names...
    proto_name = ''
    messages_dic = {}
    for proto_line in messages.split("\n"):
        if is_blank(proto_line):
            continue
        if operator.contains(proto_line, "message ") or operator.contains(proto_line, "enum ") or operator.contains(
                proto_line, "oneof ") and operator.contains(
            proto_line, "{"):
            proto_name = proto_line.split(" ")[1].strip()
        if proto_line == '':
            continue
        if operator.contains(proto_line, " result =") and len(
                proto_line.split(" ")[0].strip()) == 11 and proto_line.split(" ")[0].strip().isupper():
            messages_dic.setdefault(proto_line.split(" ")[0].strip(), "Result")
        elif operator.contains(proto_line, " status =") and len(
                proto_line.split(" ")[0].strip()) == 11 and proto_line.split(" ")[0].strip().isupper():
            messages_dic.setdefault(proto_line.split(" ")[0].strip(), "Status")
        elif operator.contains(proto_line, "CHARACTER_BLANCHE = 1;") and len(proto_name) == 11 and proto_name.isupper():
            messages_dic.setdefault(proto_name, "InvasionCharacter")

        if operator.contains(proto_line, "{") and len(proto_name) == 11 and proto_name.isupper():
            if operator.contains(proto_line, "oneof "):
                print("OneOf: " + proto_name)
            elif operator.contains(proto_line, "message "):
                print("Message: " + proto_name)
            else:
                print("Enum: " + proto_name)

    ## fix messages obfuscated names
    # print("Cleaning process on messages...")
    for _message in messages_dic:
        # print("Obfuscated message name " + _message + " clean message name " + messages_dic[_message])
        messages = messages.replace(_message, messages_dic[_message])

    ## Reorder all this...
    new_base_enums = {}
    new_base_messages = {}
    new_base_as_data = False
    new_base_is_enum = False
    new_base_proto_name = ''
    new_base_data = ''

    for proto_line in messages.split("\n"):
        if proto_line.startswith("enum") or proto_line.startswith("message"):
            new_base_as_data = True
            new_base_proto_name = proto_line.split(" ")[1]
        if proto_line.startswith("enum"):
            new_base_is_enum = True
        if proto_line.startswith("message"):
            new_base_is_enum = False
        if proto_line.startswith("}"):
            new_base_data += proto_line + "\n"
            if new_base_is_enum:
                new_base_enums.setdefault(new_base_proto_name, new_base_data)
            else:
                # fix Weather stuff
                if new_base_proto_name == "WeatherAlertProto" and not operator.contains(new_base_data, "Severity severity = 1;"):
                    new_base_data = new_base_data.replace("bool warn_weather = 2;", "Severity severity = 1;\n\tbool warn_weather = 2;")
                if new_base_proto_name == "GameplayWeatherProto" and not operator.contains(new_base_data, "WeatherCondition gameplay_condition = 1;"):
                    new_base_data = new_base_data.replace("\t}", "\t}\n\n\tWeatherCondition gameplay_condition = 1;")
                new_base_messages.setdefault(new_base_proto_name, new_base_data)
            new_base_as_data = False
            new_base_is_enum = False
            new_base_proto_name = ''
            new_base_data = ''
        if new_base_as_data:
            new_base_data += proto_line + "\n"

    new_base_file = ''
    head_file = None

    if (gen_files):
        if os.path.exists(gen_last_files):
            shutil.rmtree(gen_last_files)

        if not os.path.exists(gen_last_files):
            os.makedirs(gen_last_files)

        head_file = head.replace('*\n* Version: ' + version + '\n*\n', '*\n* Note: For references only.\n*\n')

    for p in sorted(new_base_enums):
        new_base_file += new_base_enums[p] + "\n"
        if head_file is not None:
            open_for_new_enum = open(gen_last_files + "/" + p + '.proto', 'a')
            open_for_new_enum.writelines(head_file)
            open_for_new_enum.writelines(new_base_enums[p])
            open_for_new_enum.close()
    for p in sorted(new_base_messages):
        new_base_file += new_base_messages[p] + "\n"
        if head_file is not None:
            open_for_new_message = open(gen_last_files + "/" + p + '.proto', 'a')
            open_for_new_message.writelines(head_file)
            open_for_new_message.writelines(new_base_messages[p])
            open_for_new_message.close()

    ## find imports ..
    if head_file is not None:
        for p in sorted(new_base_messages):
            yes = False
            if os.path.exists(gen_last_files + "/" + p + '.proto'):
                os.remove(gen_last_files + "/" + p + '.proto')
                yes = True

            open_for_new_message = open(gen_last_files + "/" + p + '.proto', 'a')
            open_for_new_message.writelines(head_file)
            includes = []

            for message in new_base_messages[p].split("\n"):
                if message.startswith("message") or message.startswith("enum") or message.startswith("}"):
                    continue
                file_for_includes = message.split(" ")[0].strip() + '.proto'

                if message.startswith("\trepeated"):
                    file_for_includes = message.split(" ")[1].strip() + '.proto'

                if yes and os.path.exists(gen_last_files + "/" + file_for_includes):
                    if file_for_includes not in includes:
                        includes.append(file_for_includes)

            if len(includes) > 0:
                files_inc = ''
                for file in includes:
                    files_inc += 'import "' + file + '";\n'
                if files_inc != '':
                    open_for_new_message.writelines(files_inc + '\n')

            open_for_new_message.writelines(new_base_messages[p])
            open_for_new_message.close()

    messages = new_base_file
    open_for_new.writelines(messages[:-1])
    open_for_new.close()
    add_command_for_new_proto_file(new_proto_single_file)


def add_command_for_new_proto_file(file):
    command_out_path = os.path.abspath(out_path)
    options = ''
    arguments = ''
    if lang == 'js':
        options = 'import_style=commonjs,binary'
    elif lang == 'swift':
        arguments = '--swift_opt=Visibility=Public'
    # elif lang == 'csharp':
    #    arguments = '--csharp_opt=file_extension=.g.cs --csharp_opt=base_namespace'
    # elif lang == 'dart':
    #    arguments = '--plugin "pub run protoc_plugin"'
    # elif lang == 'lua':
    #    arguments = '--plugin=protoc-gen-lua="../ProtoGenLua/plugin/build.bat"'
    elif lang == 'go':
        options = 'plugins=grpc'

    commands.append(
        """{0} --proto_path={1} --{2}_out={3}:{4} {5} {6}""".format(
            protoc_executable,
            protos_path,
            lang,
            options,
            command_out_path,
            arguments,
            file
        )
    )


compile_ext = 'proto'

if lang != 'proto':
    compile_ext = lang
elif gen_base and gen_files and gen_only:
    compile_ext = "remaster all"
elif gen_base and not gen_only and not gen_files:
    compile_ext = 'base'
elif not gen_base and gen_only and not gen_files:
    compile_ext = raw_name
elif not gen_base and not gen_only and gen_files:
    compile_ext = 'v' + version + '.proto, generate files'

print("Compile: " + compile_ext + ", please await...")
print(package_name + " " + version)
call(""""{0}" --version""".format(protoc_executable), shell=True)

open_proto_file(raw_proto_file, head)
generated_file = raw_proto_file.replace(raw_name, input_file)
descriptor_file = generated_file.replace(".proto", ".desc")
descriptor_file_arguments = ['--include_source_info', '--include_imports']

commands.append(
    """"{0}" --proto_path="{1}" --descriptor_set_out="{2}" {3} {4}""".format(
        protoc_executable,
        protos_path,
        descriptor_file,
        ' '.join(descriptor_file_arguments),
        generated_file))

if not gen_only and not gen_base and not gen_files and not lang == 'proto':
    # Compile commands
    for command in commands:
        call(command, shell=True)

    # Add new desc version
    descriptor_file = generated_file.replace(".proto", ".desc")
    shutil.move(descriptor_file, out_path)

# Add new proto version
if gen_only:
    shutil.copy(generated_file, protos_path + '/v' + version + '.proto')

# New base for next references names
if gen_base:
    try:
        os.unlink(base_file)
    except OSError:
        pass

    shutil.copy(generated_file, base_file)

if keep_file:
    shutil.move(generated_file, out_path)

if lang == 'python':
    finish_compile(out_path, lang)

# Clean genererated and unneded files
try:
    os.unlink(generated_file)
except OSError:
    pass

print("Done!")
