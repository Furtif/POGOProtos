#!/usr/bin/env python
# This Python file uses the following encoding: utf-8

import argparse
import operator
import os
import re
import shutil
from subprocess import call

# Variables
protoc_executable = "protoc"
package_name = 'POGOProtos.Rpc'
input_file = "POGOProtos.Rpc.proto"


def is_blank(my_string):
    if my_string and my_string.strip():
        return False
    return True


# args
parser = argparse.ArgumentParser()
parser.add_argument("-l", "--lang", help="Language to produce proto single file.")
parser.add_argument("-o", "--out_path", help="Output path for roto single file.")
parser.add_argument("-m", "--java_multiple_files", action='store_true',
                    help='Write each message to a separate .java file.')
parser.add_argument("-g", "--generate_only", action='store_true', help='Generates only proto compilable.')
parser.add_argument("-k", "--keep_proto_file", action='store_true', help='Do not remove .proto file after compiling.')
parser.add_argument("-r", "--rpc", action='store_true', help='Generates Rpc proto.')
parser.add_argument("-1", "--generate_one_off", action='store_true', help='Include on off')
args = parser.parse_args()

# Add licenses
head = '/*\n'
head += '* Copyright 2016-2020 --=FurtiF=--.\n'
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
head += '*/\n\n'
head += 'syntax = "proto3";\n'
head += 'package %s;\n\n' % package_name

# Set defaults
lang = args.lang or "proto"
out_path = args.out_path or "out/single_file/" + lang
java_multiple_files = args.java_multiple_files
gen_only = args.generate_only
gen_one_off = args.generate_one_off
keep_file = args.keep_proto_file
rpc = args.rpc

# Determine where path's
raw_proto_file = os.path.abspath("base/raw_protos.proto")
base_file = os.path.abspath("base/base.proto")
protos_path = os.path.abspath("base")
out_path = os.path.abspath(out_path)

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

# Re-order base
# Clean up previous base
try:
    os.remove(base_file)
except OSError:
    pass

open_for_new = open(base_file, 'a')
new_base_file = head

for p in sorted(base_enums):
    # print("Key: " + p + "\n" + base_enums[p])
    new_base_file += base_enums[p] + "\n"
for p in sorted(base_messages):
    # print("Key: " + p + "\n" + base_messages[p])
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
    new_proto_single_file = main_file.replace("raw_protos.proto", "POGOProtos.Rpc.proto")

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
    is_enum = False
    enum_name = ''
    is_one_off = False
    refs = []
    enums_dic = {}
    messages_dic = {}
    ignored_one_of = {}
    is_ignored = False
    check_sub_message_end = True
    fixed_messages = ''

    with open(main_file, 'r') as proto_file:
        for proto_line in proto_file.readlines():
            if is_ignored and operator.contains(proto_line, "//}"):
                is_ignored = False
            if operator.contains(proto_line, "//ignored_"):
                proto_line = proto_line.replace("//ignored_", "//")
                is_ignored = True
            if is_ignored and operator.contains(proto_line, "=") and not operator.contains(proto_line, "//none = 0;"):
                ignored_one_of.setdefault(proto_line.strip().split("=")[1], proto_line.strip().split("=")[0].strip())
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

            if proto_line.startswith("enum"):
                is_enum = True
                match = re.split(r'\s', proto_line)
                if match[1].isupper() and len(match[1]) == 11:
                    enum_name = match[1].upper()
                else:
                    i = 0
                    enum_name = ''
                    for x in match[1]:
                        if x.isupper() and i > 0:
                            enum_name += '_' + x
                        else:
                            enum_name += x
                        i = i + 1
                    enum_name = enum_name.upper().replace('P_O_I_', 'POI_')

            if not proto_line.startswith("enum") and not proto_line.startswith("message") and operator.contains(
                    proto_line, "enum") or operator.contains(proto_line, "message"):
                check_sub_message_end = False
            if len(ignored_one_of) > 0 and operator.contains(proto_line,
                                                             "=") and not is_ignored and not operator.contains(
                proto_line, "//") and not is_one_off and not is_enum and check_sub_message_end:
                if proto_line.strip().split("=")[1] in ignored_one_of:
                    proto_line = proto_line.replace(proto_line.strip().split("=")[0].split(" ")[1],
                                                    ignored_one_of[proto_line.strip().split("=")[1]]).replace("//", "")
                    try:
                        ignored_one_of.pop(proto_line.strip().split("=")[1], None)
                    except KeyError:
                        pass

            # refs
            if operator.contains(proto_line, "// ref:"):
                refs.append(proto_line.replace("// ref:", "").strip())
            if operator.contains(proto_line, "}") and refs:
                refs.pop()

            # OneOf stuff here
            if operator.contains(proto_line, "//oneof"):
                is_one_off = True
            # ---
            if operator.contains(proto_line, "//") and is_one_off:
                if gen_one_off:
                    if operator.contains(proto_line, "none = 0;"):
                        continue
                    proto_line = proto_line.replace("//", "")
                    if not operator.contains(proto_line, "{") and not operator.contains(proto_line, "}"):
                        field = proto_line.split("=")[0].strip()
                        refName = "/".join(refs[-1].split("/")[:-1])
                        proto_line = "#" + refName + "#" + field + "#"
                else:
                    continue
            if is_one_off and operator.contains(proto_line, "}"):
                is_one_off = False

            if is_enum:
                if not proto_line.startswith("enum"):
                    if not proto_line.startswith("}"):
                        e = proto_line.replace(re.split(r'(\W+)', proto_line)[2],
                                               enum_name + "_" + re.split(r'(\W+)', proto_line)[2])

                        ## first check ...
                        if operator.contains(e, "V0001_POKEMON_BULBASAUR = 1;"):
                            enums_dic.setdefault(enum_name, "HoloPokemonId")
                            messages = messages.replace(enum_name + "_POKEMON_UNSET = 0;", "MISSINGNO = 0;")
                            enum_name = "HOLO_POKEMON_ID"
                        elif operator.contains(e, "V0001_FAMILY_BULBASAUR = 1;"):
                            enums_dic.setdefault(enum_name, "HoloPokemonFamilyId")
                            messages = messages.replace(enum_name + "_FAMILY_UNSET = 0;", "FAMILY_UNSET = 0;")
                            enum_name = "HOLO_POKEMON_FAMILY_ID"
                        elif operator.contains(e, "V0001_MOVE_THUNDER_SHOCK = 1;"):
                            enums_dic.setdefault(enum_name, "HoloPokemonMove")
                            messages = messages.replace(enum_name + "_MOVE_UNSET = 0;", "MOVE_UNSET = 0;")
                            enum_name = "HOLO_POKEMON_MOVE"
                        elif operator.contains(e, "ACTIVITY_CATCH_LEGEND_POKEMON = 2"):
                            enums_dic.setdefault(enum_name, "HoloActivityType")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "HOLO_ACTIVITY_TYPE_IDS"
                        elif operator.contains(e, "ITEM_CATEGORY_POKEBALL = 1;"):
                            enums_dic.setdefault(enum_name, "HoloItemCategory")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "HOLO_ITEM_CATEGORY_IDS"
                        elif operator.contains(e, "ITEM_EFFECT_CAP_NO_FLEE = 1000;"):
                            enums_dic.setdefault(enum_name, "HoloItemEffect")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "HOLO_ITEM_EFFECT_IDS"
                        elif operator.contains(e, "ITEM_TYPE_POKEBALL = 1;"):
                            enums_dic.setdefault(enum_name, "HoloItemType")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "HOLO_ITEM_TYPE"
                        elif operator.contains(e, "POKEMON_CLASS_LEGENDARY = 1;"):
                            enums_dic.setdefault(enum_name, "HoloPokemonClass")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "HOLO_POKEMON_CLASS"
                        elif operator.contains(e, "POKEMON_ENC_MOVEMENT_JUMP = 1;"):
                            enums_dic.setdefault(enum_name, "HoloPokemonMovementType")
                            messages = messages.replace(enum_name + "_POKEMON_ENC_", "")
                            e = e.replace(enum_name + "_POKEMON_ENC_", "")
                            enum_name = "HOLO_POKEMON_MOVEMENT_TYPE"
                        elif operator.contains(e, "POKEMON_TYPE_NORMAL = 1;"):
                            enums_dic.setdefault(enum_name, "HoloPokemonType")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "HOLO_POKEMON_TYPE"
                        elif operator.contains(e, "ITEM_POKE_BALL = 1;"):
                            enums_dic.setdefault(enum_name, "Item")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "ITEM_IDS"
                        elif operator.contains(e, "QUEST_FIRST_CATCH_OF_THE_DAY = 1;"):
                            enums_dic.setdefault(enum_name, "QuestType")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "QUEST_TYPE"
                        elif operator.contains(e, "RAID_LEVEL_1 = 1;"):
                            enums_dic.setdefault(enum_name, "RaidLevel")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "RAID_LEVEL_IDS"
                        elif operator.contains(e, "TEAM_BLUE = 1;"):
                            enums_dic.setdefault(enum_name, "Team")
                            messages = messages.replace(enum_name + "_", "TEAM_")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "TEAM_IDS"
                        elif operator.contains(e, "TEMP_EVOLUTION_MEGA = 1;"):
                            enums_dic.setdefault(enum_name, "HoloTemporaryEvolutionId")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "HOLO_TEMPORARY_EVOLUTION_ID"
                        elif operator.contains(e, "PLAYER_AVATAR_FEMALE = 1;"):
                            enums_dic.setdefault(enum_name, "PlayerAvatarType")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "PLAYER_AVATAR_TYPE"
                        elif operator.contains(e, "BADGE_TRAVEL_KM = 1;"):
                            enums_dic.setdefault(enum_name, "HoloBadgeType")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "HOLO_BADGE_TYPE"
                        elif operator.contains(e, "IAP_CATEGORY_BUNDLE = 1;"):
                            enums_dic.setdefault(enum_name, "HoloIapItemCategory")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "HOLO_IAP_ITEM_CATEGORY_IAP"
                        elif operator.contains(e, "INCREASE_POKEMON_STORAGE = 2;"):
                            enums_dic.setdefault(enum_name, "InventoryUpgradeType")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "INVENTORY_UPGRADE_TYPE"
                        elif operator.contains(e, "QUIT = 1;"):
                            enums_dic.setdefault(enum_name, "AvatarCompletion")
                            messages = messages.replace(enum_name + "_", "AVATAR_COMPLETION_")
                            e = e.replace(enum_name + "_", "AVATAR_COMPLETION_")
                            enum_name = "AVATAR_COMPLETION"
                        elif operator.contains(e, "SUBSECTION_VS_CHARGING = 1;"):
                            enums_dic.setdefault(enum_name, "BattleHubSubsection")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "BATTLE_HUB_SUBSECTION"
                        elif operator.contains(e, "UNDEFINED_POKEMON_GO_PLUS_EVENT = 0;"):
                            enums_dic.setdefault(enum_name, "PokemonGoPlusIds")
                            messages = messages.replace(enum_name + "_", "POKEMON_GO_PLUS_IDS_")
                            e = e.replace(enum_name + "_", "POKEMON_GO_PLUS_IDS_")
                            enum_name = "POKEMON_GO_PLUS_IDS"
                        elif operator.contains(e, "DIALOG = 2;"):
                            enums_dic.setdefault(enum_name, "PhoneBoothPresentationMode")
                            messages = messages.replace(enum_name + "_", "PHONE_BOOTH_PRESENTATION_MODE_")
                            e = e.replace(enum_name + "_", "PHONE_BOOTH_PRESENTATION_MODE_")
                            enum_name = "PHONE_BOOTH_PRESENTATION_MODE"
                        elif operator.contains(e, "UNDEFINED_ASSET_EVENT = 0;"):
                            enums_dic.setdefault(enum_name, "AssetTelemetryIds")
                            messages = messages.replace(enum_name + "_", "ASSET_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "ASSET_TELEMETRY_IDS_")
                            enum_name = "ASSET_TELEMETRY_IDS"
                        elif operator.contains(e, "UNDEFINED_REMOTE_RAID_JOIN_SOURCE = 0;"):
                            enums_dic.setdefault(enum_name, "RemoteRaidJoinSource")
                            messages = messages.replace(enum_name + "_", "REMOTE_RAID_JOIN_SOURCE_")
                            e = e.replace(enum_name + "_", "REMOTE_RAID_JOIN_SOURCE_")
                            enum_name = "REMOTE_RAID_JOIN_SOURCE"
                        elif operator.contains(e, "AD_FEEDBACK_LIKE_REASON_INVALID = 0;"):
                            enums_dic.setdefault(enum_name, "AdFeedbackLikeReason")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "AD_FEEDBACK_LIKE_REASON_IDS"
                        elif operator.contains(e, "UNSET_REWARD_STATUS = 0;"):
                            enums_dic.setdefault(enum_name, "CombatRewardStatus")
                            messages = messages.replace(enum_name + "_", "COMBAT_REWARD_STATUS_")
                            e = e.replace(enum_name + "_", "COMBAT_REWARD_STATUS_")
                            enum_name = "COMBAT_REWARD_STATUS"
                        elif operator.contains(e, "UNDEFINED_PERMISSION_FLOW_STEP = 0;"):
                            enums_dic.setdefault(enum_name, "PermissionFlowStepTelemetryIds")
                            messages = messages.replace(enum_name + "_", "PERMISSION_FLOW_STEP_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "PERMISSION_FLOW_STEP_TELEMETRY_IDS_")
                            enum_name = "PERMISSION_FLOW_STEP_TELEMETRY_IDS"
                        elif operator.contains(e, "NATURE_UNKNOWN = 0;"):
                            enums_dic.setdefault(enum_name, "HoloPokemonNature")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "").replace("NATURE_", "POKEMON_NATURE_")
                            enum_name = "HOLO_POKEMON_NATURE"
                        elif operator.contains(e, "LOADING = 1;"):
                            enums_dic.setdefault(enum_name, "AssetBundleStatus")
                            messages = messages.replace(enum_name + "_", "ASSET_BUNDLE_STATUS_")
                            e = e.replace(enum_name + "_", "ASSET_BUNDLE_STATUS_")
                            enum_name = "ASSET_BUNDLE_STATUS"
                        elif operator.contains(e, "STORE_UNSET = 0;"):
                            enums_dic.setdefault(enum_name, "Store")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "STORE_IDS"
                        elif operator.contains(e, "EGG_TYPE_SHADOW = 1;"):
                            enums_dic.setdefault(enum_name, "HoloPokemonEggType")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "HOLO_POKEMON_EGG_TYPE"
                        elif operator.contains(e, "PREMIUM = 1;"):
                            enums_dic.setdefault(enum_name, "VsSeekerRewardTrack")
                            messages = messages.replace(enum_name + "_", "VS_SEEKER_REWARD_TRACK_")
                            e = e.replace(enum_name + "_", "VS_SEEKER_REWARD_TRACK_")
                            enum_name = "VS_SEEKER_REWARD_TRACK"
                        elif operator.contains(e, "_POKECOIN = 1;"):
                            enums_dic.setdefault(enum_name, "CurrencyType")
                            messages = messages.replace(enum_name + "_", "CURRENCY_TYPE_")
                            e = e.replace(enum_name + "_", "CURRENCY_TYPE_")
                            enum_name = "CURRENCY_TYPE"
                        elif operator.contains(e, "CHECKPOINT = 1;"):
                            enums_dic.setdefault(enum_name, "FortType")
                            messages = messages.replace(enum_name + "_", "FORT_TYPE_")
                            e = e.replace(enum_name + "_", "FORT_TYPE_")
                            enum_name = "FORT_TYPE"
                        elif operator.contains(e, "EXCELLENT = 4;"):
                            enums_dic.setdefault(enum_name, "VfxLevel")
                            messages = messages.replace(enum_name + "_", "VFX_LEVEL_")
                            e = e.replace(enum_name + "_", "VFX_LEVEL_")
                            enum_name = "VFX_LEVEL"
                        elif operator.contains(e, "SELECTED = 0;"):
                            enums_dic.setdefault(enum_name, "IncubatorSelectionResult")
                            messages = messages.replace(enum_name + "_", "INCUBATOR_SELECTION_RESULT_")
                            e = e.replace(enum_name + "_", "INCUBATOR_SELECTION_RESULT_")
                            enum_name = "INCUBATOR_SELECTION_RESULT"
                        elif operator.contains(e, "AD_FEEDBACK_NOT_INTERESTED_REASON_INVALID = 0;"):
                            enums_dic.setdefault(enum_name, "AdFeedbackNotInterestedReason")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "AD_FEEDBACK_NOT_INTERESTED_REASON_IDS"
                        elif operator.contains(e, "UNDEFINED_INVASION_EVENT = 0;"):
                            enums_dic.setdefault(enum_name, "InvasionTelemetryIds")
                            messages = messages.replace(enum_name + "_", "INVASION_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "INVASION_TELEMETRY_IDS_")
                            enum_name = "INVASION_TELEMETRY_IDS"
                        elif operator.contains(e, "SPAWN_POINT = 0;"):
                            enums_dic.setdefault(enum_name, "EncounterType")
                            messages = messages.replace(enum_name + "_", "ENCOUNTER_TYPE_")
                            e = e.replace(enum_name + "_", "ENCOUNTER_TYPE_")
                            enum_name = "ENCOUNTER_TYPE"
                        elif operator.contains(e, "PLATFORM_UNSET = 0;"):
                            enums_dic.setdefault(enum_name, "Platform")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "PLATFORM_IDS"
                        elif operator.contains(e, "UNDEFINED_SOCIAL = 0;"):
                            enums_dic.setdefault(enum_name, "SocialTelemetryIds")
                            messages = messages.replace(enum_name + "_", "SOCIAL_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "SOCIAL_TELEMETRY_IDS_")
                            enum_name = "SOCIAL_TELEMETRY_IDS"
                        elif operator.contains(e, "NPC = 0;"):
                            enums_dic.setdefault(enum_name, "IncidentStartContext")
                            messages = messages.replace(enum_name + "_", "INCIDENT_START_CONTEXT_")
                            e = e.replace(enum_name + "_", "INCIDENT_START_CONTEXT_")
                            enum_name = "INCIDENT_START_CONTEXT"
                        elif operator.contains(e, "SLEEP_01 = 9;"):
                            enums_dic.setdefault(enum_name, "PokemonAnim")
                            messages = messages.replace(enum_name + "_", "POKEMON_ANIM_")
                            e = e.replace(enum_name + "_", "POKEMON_ANIM_")
                            enum_name = "POKEMON_ANIM"
                        elif operator.contains(e, "UNDEFINED_REMOTE_RAID_INVITE_ACCEPT_SOURCE = 0;"):
                            enums_dic.setdefault(enum_name, "RemoteRaidInviteAcceptSource")
                            messages = messages.replace(enum_name + "_", "REMOTE_RAID_INVITE_ACCEPT_SOURCE_")
                            e = e.replace(enum_name + "_", "REMOTE_RAID_INVITE_ACCEPT_SOURCE_")
                            enum_name = "REMOTE_RAID_INVITE_ACCEPT_SOURCE"
                        elif operator.contains(e, "METHOD_UNSET = 0;"):
                            enums_dic.setdefault(enum_name, "Method")
                            messages = messages.replace(enum_name + "_", "METHOD_")
                            e = e.replace(enum_name + "_", "METHOD_")
                            enum_name = "METHOD"
                        elif operator.contains(e, "SECTION_VS_SEEKER = 1;"):
                            enums_dic.setdefault(enum_name, "BattleHubSection")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "BATTLE_HUB_SECTION"
                        elif operator.contains(e, "UNDEFINED_PERMISSION_CONTEXT = 0;"):
                            enums_dic.setdefault(enum_name, "PermissionContextTelemetryIds")
                            messages = messages.replace(enum_name + "_", "PERMISSION_CONTEXT_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "PERMISSION_CONTEXT_TELEMETRY_IDS_")
                            enum_name = "PERMISSION_CONTEXT_TELEMETRY_IDS"
                        elif operator.contains(e, "FAILURE = 1;"):
                            enums_dic.setdefault(enum_name, "IncubationResult")
                            messages = messages.replace(enum_name + "_", "INCUBATION_RESULT_")
                            e = e.replace(enum_name + "_", "INCUBATION_RESULT_")
                            enum_name = "INCUBATION_RESULT"
                        elif operator.contains(e, "UNAUTHORIZED_DEVICE = 1;"):
                            enums_dic.setdefault(enum_name, "BannedPlayerReason")
                            messages = messages.replace(enum_name + "_", "BANNED_PLAYER_REASON_")
                            e = e.replace(enum_name + "_", "BANNED_PLAYER_REASON_")
                            enum_name = "BANNED_PLAYER_REASON"
                        elif operator.contains(e, "ARSTANDARD = 1;"):
                            enums_dic.setdefault(enum_name, "ArMode")
                            messages = messages.replace(enum_name + "_", "AR_MODE_")
                            e = e.replace(enum_name + "_", "AR_MODE_")
                            enum_name = "AR_MODE"
                        elif operator.contains(e, "UNDEFINED_RAID_EVENT = 0;"):
                            enums_dic.setdefault(enum_name, "RaidTelemetryIds")
                            messages = messages.replace(enum_name + "_", "RAID_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "RAID_TELEMETRY_IDS_")
                            enum_name = "RAID_TELEMETRY_IDS"
                        elif operator.contains(e, "LEGAL_SCREEN = 0;"):
                            enums_dic.setdefault(enum_name, "TutorialCompletion")
                            messages = messages.replace(enum_name + "_", "TUTORIAL_COMPLETION_")
                            e = e.replace(enum_name + "_", "TUTORIAL_COMPLETION_")
                            enum_name = "TUTORIAL_COMPLETION"
                        elif operator.contains(e, "UNDEFINED_EVENT = 0;"):
                            enums_dic.setdefault(enum_name, "CombatHubEntranceTelemetryIds")
                            messages = messages.replace(enum_name + "_", "COMBAT_HUB_ENTRANCE_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "COMBAT_HUB_ENTRANCE_TELEMETRY_IDS_")
                            enum_name = "COMBAT_HUB_ENTRANCE_TELEMETRY_IDS"
                        elif operator.contains(e, "INVASION_GRUNT = 1;"):
                            enums_dic.setdefault(enum_name, "IncidentDisplayType")
                            messages = messages.replace(enum_name + "_", "INCIDENT_DISPLAY_TYPE_")
                            e = e.replace(enum_name + "_", "INCIDENT_DISPLAY_TYPE_")
                            enum_name = "INCIDENT_DISPLAY_TYPE"
                        elif operator.contains(e, "unset__notification_category = 0;"):
                            e = e.replace("unset__notification_category = 0;", "UNSET = 0;")
                            enums_dic.setdefault(enum_name, "NotificationCategory")
                            messages = messages.replace(enum_name + "_", "NOTIFICATION_CATEGORY_")
                            e = e.replace(enum_name + "_", "NOTIFICATION_CATEGORY_")
                            enum_name = "NOTIFICATION_CATEGORY"
                        elif operator.contains(e, "AR_STANDARD = 2;"):
                            enums_dic.setdefault(enum_name, "OnboardingArStatus")
                            messages = messages.replace(enum_name + "_", "ONBOARDING_AR_STATUS_")
                            e = e.replace(enum_name + "_", "ONBOARDING_AR_STATUS_")
                            enum_name = "ONBOARDING_AR_STATUS"
                        elif operator.contains(e, "CREATE_CONTEXT_WILD = 0;"):
                            enums_dic.setdefault(enum_name, "PokemonCreateContext")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "POKEMON_CREATE_CONTEXT"
                        elif operator.contains(e, "GEN8 = 7;"):
                            enums_dic.setdefault(enum_name, "PokedexGenerationId")
                            messages = messages.replace(enum_name + "_", "POKEDEX_GENERATION_ID_")
                            e = e.replace(enum_name + "_", "POKEDEX_GENERATION_ID_")
                            enum_name = "POKEDEX_GENERATION_ID"
                        elif operator.contains(e, "GREETING = 0;"):
                            enums_dic.setdefault(enum_name, "IncidentDynamicStringTypes")
                            messages = messages.replace(enum_name + "_", "INCIDENT_DYNAMIC_STRING_TYPES_")
                            e = e.replace(enum_name + "_", "INCIDENT_DYNAMIC_STRING_TYPES_")
                            enum_name = "INCIDENT_DYNAMIC_STRING_TYPES"
                        elif operator.contains(e, "ADD = 0;"):
                            enums_dic.setdefault(enum_name, "UpdateType")
                            messages = messages.replace(enum_name + "_", "UPDATE_TYPE_")
                            e = e.replace(enum_name + "_", "UPDATE_TYPE_")
                            enum_name = "UPDATE_TYPE"
                        elif operator.contains(e, "BUDDY_ANIMATION_UNSET = 0;"):
                            enums_dic.setdefault(enum_name, "BuddyAnimation")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "BUDDY_ANIMATION_IDS"
                        elif operator.contains(e, "UNDEFINED_SHOPPING_PAGE_EVENT = 0;"):
                            enums_dic.setdefault(enum_name, "ShoppingPageTelemetryIds")
                            messages = messages.replace(enum_name + "_", "SHOPPING_PAGE_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "SHOPPING_PAGE_TELEMETRY_IDS_")
                            enum_name = "SHOPPING_PAGE_TELEMETRY_IDS"
                        elif operator.contains(e, "BUDDY_ACTIVITY_UNSET = 0;"):
                            enums_dic.setdefault(enum_name, "BuddyActivity")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "BUDDY_ACTIVITY_IDS"
                        elif operator.contains(e, "GYM_BADGE_UNSET = 0;"):
                            enums_dic.setdefault(enum_name, "GymBadgeType")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "GYM_BADGE_TYPE_IDS"
                        elif operator.contains(e, "UNDEFINED_PROFILE_PAGE = 0;"):
                            enums_dic.setdefault(enum_name, "ProfilePageTelemetryIds")
                            messages = messages.replace(enum_name + "_", "PROFILE_PAGE_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "PROFILE_PAGE_TELEMETRY_IDS_")
                            enum_name = "PROFILE_PAGE_TELEMETRY_IDS"
                        elif operator.contains(e, "COMBAT_TYPE_UNSET = 0;"):
                            enums_dic.setdefault(enum_name, "CombatType")
                            messages = messages.replace(enum_name + "_", "COMBAT_TYPE_")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "COMBAT_TYPE"
                        elif operator.contains(e, "WINNER = 0;"):
                            enums_dic.setdefault(enum_name, "CombatPlayerFinishState")
                            messages = messages.replace(enum_name + "_", "COMBAT_PLAYER_FINISH_STATE_")
                            e = e.replace(enum_name + "_", "COMBAT_PLAYER_FINISH_STATE_")
                            enum_name = "COMBAT_PLAYER_FINISH_STATE"
                        elif operator.contains(e, "UNDEFINED_MAP_EVENT = 0;"):
                            enums_dic.setdefault(enum_name, "MapEventsTelemetryIds")
                            messages = messages.replace(enum_name + "_", "MAP_EVENTS_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "MAP_EVENTS_TELEMETRY_IDS_")
                            enum_name = "MAP_EVENTS_TELEMETRY_IDS"
                        elif operator.contains(e, "CAM_INTERP_CUT = 0;"):
                            enums_dic.setdefault(enum_name, "CameraInterpolation")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "CAMERA_INTERPOLATION"
                        elif operator.contains(e, "WHAT_IS_POKESTOP = 0;"):
                            enums_dic.setdefault(enum_name, "PoiSubmissionTutorialPage")
                            messages = messages.replace(enum_name + "_", "POI_SUBMISSION_TUTORIAL_PAGE_")
                            e = e.replace(enum_name + "_", "POI_SUBMISSION_TUTORIAL_PAGE_")
                            enum_name = "POI_SUBMISSION_TUTORIAL_PAGE"
                        elif operator.contains(e, "ENCOUNTER = 0;"):
                            enums_dic.setdefault(enum_name, "ArToggleContext")
                            messages = messages.replace(enum_name + "_", "AR_TOGGLE_CONTEXT_")
                            e = e.replace(enum_name + "_", "AR_TOGGLE_CONTEXT_")
                            enum_name = "AR_TOGGLE_CONTEXT"
                        elif operator.contains(e, "UNDEFINED_DEVICE_SERVICE = 0;"):
                            enums_dic.setdefault(enum_name, "DeviceServiceTelemetryIds")
                            messages = messages.replace(enum_name + "_", "DEVICE_SERVICE_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "DEVICE_SERVICE_TELEMETRY_IDS_")
                            enum_name = "DEVICE_SERVICE_TELEMETRY_IDS"
                        elif operator.contains(e, "_BOOT_TIME = 1;"):
                            enums_dic.setdefault(enum_name, "HoloholoClientTelemetryIds")
                            messages = messages.replace(enum_name + "_", "HOLOHOLO_CLIENT_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "HOLOHOLO_CLIENT_TELEMETRY_IDS_")
                            enum_name = "HOLOHOLO_CLIENT_TELEMETRY_IDS"
                        elif operator.contains(e, "unset__variable_name = 0;"):
                            e = e.replace("unset__variable_name = 0;", "UNSET = 0;")
                            enums_dic.setdefault(enum_name, "VariableName")
                            messages = messages.replace(enum_name + "_", "VARIABLE_NAME_")
                            e = e.replace(enum_name + "_", "VARIABLE_NAME_")
                            enum_name = "VARIABLE_NAME"
                        elif operator.contains(e, "FOLLOW_X = 1;"):
                            enums_dic.setdefault(enum_name, "POIDecorationFollowFlags")
                            messages = messages.replace(enum_name + "_" + enum_name + "_",
                                                        "POI_DECORATION_FOLLOW_FLAGS_")
                            e = e.replace(enum_name + "_", "POI_DECORATION_FOLLOW_FLAGS_")
                            enum_name = "POI_DECORATION_FOLLOW_FLAGS"
                        elif operator.contains(e, "UNDEFINED_GENERIC_EVENT = 0;"):
                            enums_dic.setdefault(enum_name, "GenericClickTelemetryIds")
                            messages = messages.replace(enum_name + "_", "GENERIC_CLICK_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "GENERIC_CLICK_TELEMETRY_IDS_")
                            enum_name = "GENERIC_CLICK_TELEMETRY_IDS"
                        elif operator.contains(e, "FRIENDSHIP_LEVEL_UNSET = 0;"):
                            enums_dic.setdefault(enum_name, "FriendshipLevelMilestone")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "FRIENDSHIP_LEVEL_MILESTONE_IDS"
                        elif operator.contains(e, "PERMISSION_DENIED = -2;"):
                            enums_dic.setdefault(enum_name, "CalendarAddResult")
                            messages = messages.replace(enum_name + "_", "CALENDAR_ADD_RESULT_")
                            e = e.replace(enum_name + "_", "CALENDAR_ADD_RESULT_")
                            enum_name = "CALENDAR_ADD_RESULT"
                        elif operator.contains(e, "POKEMON_BADGE_BEST_BUDDY = 1;"):
                            enums_dic.setdefault(enum_name, "PokemonBadge")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "POKEMON_BADGE_IDS"
                        elif operator.contains(e, "METRIC_STEP = 1;"):
                            enums_dic.setdefault(enum_name, "MetricType")
                            messages = messages.replace(enum_name + "_", "METRIC_TYPE_")
                            e = e.replace(enum_name + "_", "METRIC_TYPE_")
                            enum_name = "METRIC_TYPE"
                        elif operator.contains(e, "UNDEFINED_ITEM_EVENT = 0;"):
                            enums_dic.setdefault(enum_name, "ItemUseTelemetryIds")
                            messages = messages.replace(enum_name + "_", "ITEM_USE_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "ITEM_USE_TELEMETRY_IDS_")
                            enum_name = "ITEM_USE_TELEMETRY_IDS"
                        elif operator.contains(e, "UNDEFINED_REMOTE_RAID_EVENT = 0;"):
                            enums_dic.setdefault(enum_name, "RemoteRaidTelemetryIds")
                            messages = messages.replace(enum_name + "_", "REMOTE_RAID_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "REMOTE_RAID_TELEMETRY_IDS_")
                            enum_name = "REMOTE_RAID_TELEMETRY_IDS"
                        elif operator.contains(e, "CAM_TARGET_ATTACKER = 0;"):
                            enums_dic.setdefault(enum_name, "CameraTarget")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "CAMERA_TARGET"
                        elif operator.contains(e, "UNDEFINED_POKEMON_INVENTORY_EVENT = 0;"):
                            enums_dic.setdefault(enum_name, "PokemonInventoryTelemetryIds")
                            messages = messages.replace(enum_name + "_", "POKEMON_INVENTORY_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "POKEMON_INVENTORY_TELEMETRY_IDS_")
                            enum_name = "POKEMON_INVENTORY_TELEMETRY_IDS"
                        elif operator.contains(e, "SALE = 3;"):
                            enums_dic.setdefault(enum_name, "PresentationType")
                            messages = messages.replace(enum_name + "_", "PRESENTATION_TYPE_")
                            e = e.replace(enum_name + "_", "PRESENTATION_TYPE_")
                            enum_name = "PRESENTATION_TYPE"
                        elif operator.contains(e, "ENEMY_POKEMON_FOCUS = 2;"):
                            enums_dic.setdefault(enum_name, "CameraType")
                            messages = messages.replace(enum_name + "_", "CAMERA_TYPE_")
                            e = e.replace(enum_name + "_", "CAMERA_TYPE_")
                            enum_name = "CAMERA_TYPE"
                        elif operator.contains(e, "TOS_ACCEPTED = 0;"):
                            enums_dic.setdefault(enum_name, "OnboardingEventIds")
                            messages = messages.replace(enum_name + "_", "ONBOARDING_EVENT_IDS_")
                            e = e.replace(enum_name + "_", "ONBOARDING_EVENT_IDS_")
                            enum_name = "ONBOARDING_EVENT_IDS"
                        elif operator.contains(e, "PROF = 0;"):
                            enums_dic.setdefault(enum_name, "Speaker")
                            messages = messages.replace(enum_name + "_", "SPEAKER_")
                            e = e.replace(enum_name + "_", "SPEAKER_")
                            enum_name = "SPEAKER"
                        elif operator.contains(e, "UNDEFINED_WEB_EVENT = 0;"):
                            enums_dic.setdefault(enum_name, "WebTelemetryIds")
                            messages = messages.replace(enum_name + "_", "WEB_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "WEB_TELEMETRY_IDS_")
                            enum_name = "WEB_TELEMETRY_IDS"
                        elif operator.contains(e, "UNDEFINED_BATTLE_PARTY_EVENT = 0;"):
                            enums_dic.setdefault(enum_name, "BattlePartyTelemetryIds")
                            messages = messages.replace(enum_name + "_", "BATTLE_PARTY_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "BATTLE_PARTY_TELEMETRY_IDS_")
                            enum_name = "BATTLE_PARTY_TELEMETRY_IDS"
                        elif operator.contains(e, "COLOR = 0;"):
                            enums_dic.setdefault(enum_name, "POIDecorationProperties")
                            messages = messages.replace(enum_name + "_", "POI_DECORATION_PROPERTIES_")
                            e = e.replace(enum_name + "_", "POI_DECORATION_PROPERTIES_")
                            enum_name = "POI_DECORATION_PROPERTIES"
                        elif operator.contains(e, "UNDEFINED_LOGIN_ACTION = 0;"):
                            enums_dic.setdefault(enum_name, "LoginActionTelemetryIds")
                            messages = messages.replace(enum_name + "_", "LOGIN_ACTION_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "LOGIN_ACTION_TELEMETRY_IDS_")
                            enum_name = "LOGIN_ACTION_TELEMETRY_IDS"
                        elif operator.contains(e, "BUDDY_LEVEL_UNSET = 0;"):
                            enums_dic.setdefault(enum_name, "BuddyLevel")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "BUDDY_LEVEL_IDS"
                        elif operator.contains(e, "AD_FEEDBACK_COMPLAINT_REASON_INVALID = 0;"):
                            enums_dic.setdefault(enum_name, "AdFeedbackComplaintReason")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "AD_FEEDBACK_COMPLAINT_REASON_IDS"
                        elif operator.contains(e, "COMBAT_VS_SEEKER_CHARGED = 30;"):
                            enums_dic.setdefault(enum_name, "ClientInboxServiceNotificationCategory")
                            messages = messages.replace(enum_name + "_", "CLIENT_INBOX_SERVICE_NOTIFICATION_CATEGORY_")
                            e = e.replace(enum_name + "_", "CLIENT_INBOX_SERVICE_NOTIFICATION_CATEGORY_")
                            enum_name = "CLIENT_INBOX_SERVICE_NOTIFICATION_CATEGORY"
                        elif operator.contains(e, "BUDDY_CATEGORY_UNSET = 0;"):
                            enums_dic.setdefault(enum_name, "BuddyActivityCategory")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "BUDDY_ACTIVITY_CATEGORY_IDS"
                        elif operator.contains(e, "CHEAT_WARNING = 0;"):
                            enums_dic.setdefault(enum_name, "WarnedPlayerReason")
                            messages = messages.replace(enum_name + "_", "WARNED_PLAYER_REASON_")
                            e = e.replace(enum_name + "_", "WARNED_PLAYER_REASON_")
                            enum_name = "WARNED_PLAYER_REASON"
                        elif operator.contains(e, "LEAVE_GYM = 0;"):
                            enums_dic.setdefault(enum_name, "BattleResultsExit")
                            messages = messages.replace(enum_name + "_", "BATTLE_RESULTS_EXIT_")
                            e = e.replace(enum_name + "_", "BATTLE_RESULTS_EXIT_")
                            enum_name = "BATTLE_RESULTS_EXIT"
                        elif operator.contains(e, "BUDDY_EMOTION_LEVEL_UNSET = 0;"):
                            enums_dic.setdefault(enum_name, "BuddyEmotionLevel")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "BUDDY_EMOTION_LEVEL_IDS"
                        elif operator.contains(e, "V1 = 0;"):
                            enums_dic.setdefault(enum_name, "OnboardingPathIds")
                            messages = messages.replace(enum_name + "_", "ONBOARDING_PATH_IDS_")
                            e = e.replace(enum_name + "_", "ONBOARDING_PATH_IDS_")
                            enum_name = "ONBOARDING_PATH_IDS"
                        elif operator.contains(e, "SHARE_EX_RAID_PASS_UNSET = 0;"):
                            enums_dic.setdefault(enum_name, "ShareExRaidPassResult")
                            messages = messages.replace(enum_name + "_", "SHARE_EX_RAID_PASS_RESULT_")
                            e = e.replace(enum_name + "_", "SHARE_EX_RAID_PASS_RESULT_")
                            enum_name = "SHARE_EX_RAID_PASS_RESULT"
                        elif operator.contains(e, "INCUBATOR_UNSET = 0;"):
                            enums_dic.setdefault(enum_name, "EggIncubatorType")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "EGG_INCUBATOR_TYPE_IDS"
                        elif operator.contains(e, "UNDEFINED_SHOPPING_PAGE_SCROLL_TYPE = 0;"):
                            enums_dic.setdefault(enum_name, "ShoppingPageScrollIds")
                            messages = messages.replace(enum_name + "_", "SHOPPING_PAGE_SCROLL_IDS_")
                            e = e.replace(enum_name + "_", "SHOPPING_PAGE_SCROLL_IDS_")
                            enum_name = "SHOPPING_PAGE_SCROLL_IDS"
                        elif operator.contains(e, "UNDEFINED_AVATAR_CUSTOMIZATION = 0;"):
                            enums_dic.setdefault(enum_name, "AvatarCustomizationTelemetryIds")
                            messages = messages.replace(enum_name + "_", "AVATAR_CUSTOMIZATION_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "AVATAR_CUSTOMIZATION_TELEMETRY_IDS_")
                            enum_name = "AVATAR_CUSTOMIZATION_TELEMETRY_IDS"
                        elif operator.contains(e, "V1 = 1;"):
                            enums_dic.setdefault(enum_name, "PlayerOnboardingPath")
                            messages = messages.replace(enum_name + "_", "PLAYER_ONBOARDING_PATH_")
                            e = e.replace(enum_name + "_", "PLAYER_ONBOARDING_PATH_")
                            enum_name = "PLAYER_ONBOARDING_PATH"
                        elif operator.contains(e, "UNDEFINED_PUSH_NOTIFICATION_EVENT = 0;"):
                            enums_dic.setdefault(enum_name, "PushNotificationTelemetryIds")
                            messages = messages.replace(enum_name + "_", "PUSH_NOTIFICATION_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "PUSH_NOTIFICATION_TELEMETRY_IDS_")
                            enum_name = "PUSH_NOTIFICATION_TELEMETRY_IDS"
                        elif operator.contains(e, "SOUVENIR_UNSET = 0;"):
                            enums_dic.setdefault(enum_name, "SouvenirTypeId")
                            messages = messages.replace(enum_name + "_", "")
                            e = e.replace(enum_name + "_", "")
                            enum_name = "SOUVENIR_TYPE_ID"
                        elif operator.contains(e, "UNDEFINED_SHOPPING_PAGE_SOURCE = 0;"):
                            enums_dic.setdefault(enum_name, "ShoppingPageTelemetrySource")
                            messages = messages.replace(enum_name + "_", "SHOPPING_PAGE_TELEMETRY_SOURCE_")
                            e = e.replace(enum_name + "_", "SHOPPING_PAGE_TELEMETRY_SOURCE_")
                            enum_name = "SHOPPING_PAGE_TELEMETRY_SOURCE"
                        elif operator.contains(e, "EXCELLENT = 3;"):
                            enums_dic.setdefault(enum_name, "CameraZoomInLevel")
                            messages = messages.replace(enum_name + "_", "CAMERA_ZOOM_IN_LEVEL_")
                            e = e.replace(enum_name + "_", "CAMERA_ZOOM_IN_LEVEL_")
                            enum_name = "CAMERA_ZOOM_IN_LEVEL"
                        elif operator.contains(e, "SINGLE = 0;"):
                            enums_dic.setdefault(enum_name, "AnimationTake")
                            messages = messages.replace(enum_name + "_", "ANIMATION_TAKE_")
                            e = e.replace(enum_name + "_", "ANIMATION_TAKE_")
                            enum_name = "ANIMATION_TAKE"
                        elif operator.contains(e, "ONBOARDING_INTRODUCTION = 0;"):
                            enums_dic.setdefault(enum_name, "IncidentLeaderStringTypes")
                            messages = messages.replace(enum_name + "_", "INCIDENT_LEADER_STRING_TYPES_")
                            e = e.replace(enum_name + "_", "INCIDENT_LEADER_STRING_TYPES_")
                            enum_name = "INCIDENT_LEADER_STRING_TYPES"
                        elif operator.contains(e, "UNDEFINED_NEWS_EVENT = 0;"):
                            enums_dic.setdefault(enum_name, "NewsPageTelemetryIds")
                            messages = messages.replace(enum_name + "_", "NEWS_PAGE_TELEMETRY_IDS_")
                            e = e.replace(enum_name + "_", "NEWS_PAGE_TELEMETRY_IDS_")
                            enum_name = "NEWS_PAGE_TELEMETRY_IDS"
                        elif operator.contains(e, "SURROUNDING = 2;") and len(enum_name) == 11 and enum_name.isupper():
                            enums_dic.setdefault(enum_name, "TitanPoiImageType")
                            messages = messages.replace(enum_name + "_", "TITAN_POI_IMAGE_TYPE_")
                            e = e.replace(enum_name + "_", "TITAN_POI_IMAGE_TYPE_")
                            enum_name = "TITAN_POI_IMAGE_TYPE"
                        elif operator.contains(e, "_VICTORY = 1;") and messages[:-1].endswith("_NONE = 0;"):
                            enums_dic.setdefault(enum_name, "IncidentFinishSequence")
                            messages = messages.replace(enum_name + "_", "INCIDENT_FINISH_SEQUENCE_")
                            e = e.replace(enum_name + "_", "INCIDENT_FINISH_SEQUENCE_")
                            enum_name = "INCIDENT_FINISH_SEQUENCE"
                        elif operator.contains(e, "_VICTORY = 1;") and messages[:-1].endswith("_NORMAL = 0;"):
                            enums_dic.setdefault(enum_name, "ExitVfxContext")
                            messages = messages.replace(enum_name + "_", "EXIT_VFX_CONTEXT_")
                            e = e.replace(enum_name + "_", "EXIT_VFX_CONTEXT_")
                            enum_name = "EXIT_VFX_CONTEXT"

                        ## second check ...
                        if enum_name == "HOLO_POKEMON_ID":
                            e = e.replace(enum_name + "_", "")
                            if operator.contains(e, "_POKEMON_"):
                                e = e.replace(e.split("_POKEMON_")[0].strip(), "").replace("_POKEMON_", "")
                                if operator.contains(e, "NIDORAN") and operator.contains(e, "= 29;"):
                                    e = e.replace("NIDORAN", "NIDORAN_FEMALE")
                                elif operator.contains(e, "NIDORAN") and operator.contains(e, "= 32;"):
                                    e = e.replace("NIDORAN", "NIDORAN_MALE")
                        elif enum_name == "HOLO_POKEMON_MOVE":
                            e = e.replace(enum_name + "_", "")
                            if operator.contains(e, "_MOVE_"):
                                e = e.replace(e.split("_MOVE_")[0].strip(), "").replace("_MOVE_", "")
                        elif enum_name == "HOLO_TEMPORARY_EVOLUTION_ID":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "HOLO_ITEM_TYPE":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "HOLO_POKEMON_CLASS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "ITEM_IDS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "HOLO_IAP_ITEM_CATEGORY_IAP":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "PLAYER_AVATAR_TYPE":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "HOLO_BADGE_TYPE":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "HOLO_POKEMON_FAMILY_ID":
                            e = e.replace(enum_name + "_", "")
                            if not operator.contains(e, "= 0;"):
                                e = e.replace(e.split("_FAMILY_")[0].strip(), "").replace("_FAMILY_", "FAMILY_")
                                if operator.contains(e, "NIDORAN") and operator.contains(e, "= 29;"):
                                    e = e.replace("NIDORAN", "NIDORAN_FEMALE")
                                elif operator.contains(e, "NIDORAN") and operator.contains(e, "= 32;"):
                                    e = e.replace("NIDORAN", "NIDORAN_MALE")
                        elif enum_name == "HOLO_POKEMON_NATURE":
                            e = e.replace(enum_name + "_", "")
                            if not operator.contains(e, "= 0;"):
                                e = e.replace(e.split("_POKEMON_")[0].strip(), "").replace("_POKEMON_", "POKEMON_")
                        elif enum_name == "HOLO_POKEMON_MOVEMENT_TYPE":
                            e = e.replace(enum_name + "_POKEMON_ENC_", "")
                        elif enum_name == "HOLO_POKEMON_TYPE":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "QUEST_TYPE":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "RAID_LEVEL_IDS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "BUDDY_ANIMATION_IDS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "STORE_IDS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "AD_FEEDBACK_NOT_INTERESTED_REASON_IDS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "AD_FEEDBACK_LIKE_REASON_IDS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "CAMERA_TARGET":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "CAMERA_INTERPOLATION":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "BUDDY_LEVEL_IDS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "AD_FEEDBACK_COMPLAINT_REASON_IDS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "BUDDY_EMOTION_LEVEL_IDS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "BUDDY_ACTIVITY_IDS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "BUDDY_ACTIVITY_CATEGORY_IDS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "GYM_BADGE_TYPE_IDS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "FRIENDSHIP_LEVEL_MILESTONE_IDS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "BATTLE_HUB_SECTION":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "BATTLE_HUB_SUBSECTION":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "PLATFORM_IDS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "POKEMON_BADGE_IDS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "HOLO_ITEM_CATEGORY_IDS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "SOUVENIR_TYPE_ID":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "HOLO_ACTIVITY_TYPE_IDS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "HOLO_ITEM_EFFECT_IDS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "EGG_INCUBATOR_TYPE_IDS":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "POKEMON_CREATE_CONTEXT":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "INVENTORY_UPGRADE_TYPE":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "HOLO_POKEMON_EGG_TYPE":
                            e = e.replace(enum_name + "_", "")
                        elif enum_name == "TEAM_IDS":
                            e = e.replace(enum_name + "_", "")

                        proto_line = e

            if not is_one_off and gen_one_off and operator.contains(proto_line, "=") and refs:
                split = proto_line.strip().split(" ", 2)
                field = split[1].strip()
                target = "#" + refs[-1] + "#" + field + "#"
                if target in messages:
                    messages = messages.replace(target, "\t" + proto_line)
                    continue

            messages += proto_line

            if not proto_line.startswith("}") and operator.contains(proto_line, "}"):
                check_sub_message_end = True
                messages += "\n"
                is_one_off = False
                is_enum = False

            if proto_line.startswith("}"):
                messages += "\n"
                is_enum = False
                enum_name = ''
                is_one_off = False
                ignored_one_of.clear()

    ## fix enums names
    print("Cleaning process on enums...")
    for _enum in enums_dic:
        print("Obfuscated enum name " + _enum + " clean enum name " + enums_dic[_enum])
        messages = messages.replace(_enum, enums_dic[_enum])

    if gen_one_off:
        messagesNew = ""
        lastLine = ""

        refs = []
        is_one_off = False
        skip = False
        setSkipFalse = False
        removeLast = False

        refsCount = {}
        for proto_line in messages.split("\n"):
            if operator.contains(proto_line, "// ref:"):
                refs.append(proto_line.replace("// ref:", "").strip())

            if operator.contains(proto_line, "}") and refs:
                refs.pop()

            if operator.contains(proto_line, "oneof") and refs:
                is_one_off = True
                count = len(messages.split("// ref: " + refs[-1] + "\n")) - 1
                if not refs[-1] in refsCount:
                    refsCount[refs[-1]] = 0
                refsCount[refs[-1]] += 1
                if not count == refsCount[refs[-1]]:
                    skip = True
                    removeLast = True

            if is_one_off and operator.contains(proto_line, "}"):
                is_one_off = False
                setSkipFalse = True

            if not skip and not (
                    (operator.contains(proto_line, "// ref:") or operator.contains(proto_line, "//----")) and gen_only):
                if not removeLast:
                    messagesNew += lastLine
                removeLast = False
                lastLine = proto_line + "\n"
            elif skip:
                removeLast = False

            if setSkipFalse:
                skip = False
                setSkipFalse = False

        messages = messagesNew

    ## check messages first
    proto_name = ''
    for proto_line in messages.split("\n"):
        if is_blank(proto_line):
            continue
        if proto_line.startswith("message"):
            proto_name = proto_line.split(" ")[1]
        if proto_line == '':
            continue
        if operator.contains(proto_line, "generic_click_telemetry = 3;"):
            messages_dic.setdefault(proto_name, "HoloholoClientTelemetryOmniProto")
        elif operator.contains(proto_line, "ERROR_PLAYER_HAS_NO_STICKERS = 8;"):
            messages_dic.setdefault(proto_name, "SendGiftOutProto")
        elif operator.contains(proto_line, "ERROR_LOBBY_EXPIRED = 14;"):
            messages_dic.setdefault(proto_name, "JoinLobbyOutProto")
        elif operator.contains(proto_line, "ERROR_INSUFFICIENT_RESOURCES = 5;"):
            messages_dic.setdefault(proto_name, "UnlockPokemonMoveOutProto")
        elif operator.contains(proto_line, "pokemon_candy = 4;"):
            messages_dic.setdefault(proto_name, "LootItemProto")
        elif operator.contains(proto_line, "pokedex_entry = 3;"):
            messages_dic.setdefault(proto_name, "HoloInventoryItemProto")
        elif operator.contains(proto_line, "pokedex_entry_id = 3;"):
            messages_dic.setdefault(proto_name, "HoloInventoryKeyProto")

    ## fix messages names
    print("Cleaning process on messages...")
    for _message in messages_dic:
        print("Obfuscated message name " + _message + " clean message name " + messages_dic[_message])
        messages = messages.replace(_message, messages_dic[_message])

    message_for_fix = None

    for fix_line in messages.split("\n"):
        # ignore refs
        if fix_line.startswith("message"):
            match = re.split(r'\s', fix_line)
            message_for_fix = match[1]
        elif fix_line.startswith("enum"):
            match = re.split(r'\s', fix_line)
            message_for_fix = match[1]

        ## Check for all bytes refs
        # if operator.contains(fix_line, "\tbytes"):
        #     byte = fix_line.split("=")
        #     byte_fix = byte[0].replace("\t","")[:-1]
        #     print('elif message_for_fix == "' + message_for_fix + '" and operator.contains(fix_line, "' + byte_fix +'"):')
        #     print('\tfix_line = fix_line.replace("bytes", "Good_Proto_Here")')

        # Replace bytes for good proto here by condition
        # if message_for_fix == "ClientGameMasterTemplateProto" and operator.contains(fix_line, "bytes data"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "BackgroundToken" and operator.contains(fix_line, "bytes token"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "BackgroundToken" and operator.contains(fix_line, "bytes iv"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "InventoryItemProto" and operator.contains(fix_line, "bytes deleted_item_key"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "InventoryItemProto" and operator.contains(fix_line, "bytes item"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "ProxyRequestProto" and operator.contains(fix_line, "bytes payload"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "ProxyResponseProto" and operator.contains(fix_line, "bytes payload"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "CJOJGABMFPD" and operator.contains(fix_line, "bytes gkbagaidnki"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "CPGAILBKMIE" and operator.contains(fix_line, "bytes dbfmaclhflp"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "DAMCNEKILPL" and operator.contains(fix_line, "bytes mlghifehoah"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "FitnessReportProto" and operator.contains(fix_line, "bytes game_data"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "FJMIKJFMAAP" and operator.contains(fix_line, "bytes fmidiibcmlp"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "HBPEACAIODI" and operator.contains(fix_line, "bytes mdnhcfkhmpj"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "IEJJEJEBLHB" and operator.contains(fix_line, "bytes dbfmaclhflp"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "JBLBFLKNFPL" and operator.contains(fix_line, "bytes clhhgpcpfal"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "JFGDKGLEJDK" and operator.contains(fix_line, "bytes clhhgpcpfal"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "JGGNAANFMKJ" and operator.contains(fix_line, "bytes mjpeknofebo"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "JGGNAANFMKJ" and operator.contains(fix_line, "bytes odoaokjbbni"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "KFMPBNDFOOJ" and operator.contains(fix_line, "bytes dbfmaclhflp"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "MECGHHCIGAO" and operator.contains(fix_line, "bytes apibanmfegp"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "OBFGGMFMJDB" and operator.contains(fix_line, "bytes dbfmaclhflp"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "ODENGIIEGNB" and operator.contains(fix_line, "bytes gkbagaidnki"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "OEFEGPKJFFO" and operator.contains(fix_line, "bytes mlghifehoah"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "OMELPMNEODN" and operator.contains(fix_line, "bytes mbopgfdlmol"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "PCDOMMOHALD" and operator.contains(fix_line, "bytes aohfihankjc"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "PCDOMMOHALD" and operator.contains(fix_line, "bytes demnjojbgli"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "PFPJGDJKEKH" and operator.contains(fix_line, "bytes mlghifehoah"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "PlatformClientApiSettingsProto" and operator.contains(fix_line, "bytes payload"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "RedeemPasscodeResponseProto" and operator.contains(fix_line, "bytes acquired_items_proto"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "AddLoginActionProto" and operator.contains(fix_line, "bytes inner_message"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "DownloadSettingsResponseProto" and operator.contains(fix_line, "bytes values"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "FriendDetailsProto" and operator.contains(fix_line, "bytes friend_visible_data"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "FriendDetailsProto" and operator.contains(fix_line, "bytes data_with_me"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "GetFriendsListOutProto" and operator.contains(fix_line, "bytes data_with_me"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "GetFriendsListOutProto" and operator.contains(fix_line, "bytes shared_data"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "GetFriendsListOutProto" and operator.contains(fix_line, "bytes data_from_me"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "GetFriendsListOutProto" and operator.contains(fix_line, "bytes data_to_me"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "PlayerSummaryProto" and operator.contains(fix_line, "bytes public_data"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "TemplateVariable" and operator.contains(fix_line, "bytes byte_value"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "ClientTelemetryRecordProto" and operator.contains(fix_line, "bytes encoded_message"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")
        # elif message_for_fix == "MapTileDataProto" and operator.contains(fix_line, "bytes tile_data"):
        #     fix_line = fix_line.replace("bytes", "Good_Proto_Here")

        fixed_messages += fix_line + "\n"

    messages = fixed_messages[:-1]

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


# print("Protocol Buffers version:")
# call(""""{0}" --version""".format(protoc_executable), shell=True)

open_proto_file(raw_proto_file, head)
generated_file = raw_proto_file.replace("raw_protos.proto", input_file)
descriptor_file = generated_file.replace(".proto", ".desc")
descriptor_file_arguments = ['--include_source_info', '--include_imports']

commands.append(
    """"{0}" --proto_path="{1}" --descriptor_set_out="{2}" {3} {4}""".format(
        protoc_executable,
        protos_path,
        descriptor_file,
        ' '.join(descriptor_file_arguments),
        generated_file))

if not gen_only:
    # Compile commands
    for command in commands:
        call(command, shell=True)

# Add new proto version
if gen_only:
    if rpc:
        dir_rpc = 'src/' + input_file.replace('.proto', '').replace('.', '/')
        if os.path.exists(dir_rpc):
            shutil.rmtree(dir_rpc)

        if not os.path.exists(dir_rpc):
            os.makedirs(dir_rpc)

        shutil.copy(generated_file, dir_rpc + '/Rpc.proto')
    shutil.copy(generated_file, protos_path + '/v0.189.0_obf.proto')
    shutil.move(generated_file, out_path)

if keep_file:
    shutil.move(generated_file, out_path)

# Add new desc version
if not gen_only:
    descriptor_file = generated_file.replace(".proto", ".desc")
    shutil.move(descriptor_file, out_path)

if lang == 'python':
    finish_compile(out_path, lang)

# Clean genererated and unneded files
try:
    os.unlink(generated_file)
except OSError:
    pass

# print("Done!")
