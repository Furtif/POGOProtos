<!-- define variables -->
[1.1]: http://i.imgur.com/M4fJ65n.png (ATTENTION)

POGOProtos [![Build Status](https://travis-ci.com/Furtif/POGOProtos.svg?branch=master)](https://travis-ci.com/Furtif/POGOProtos) [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.me/rocketbot) <!-- [![Maintainability](https://api.codeclimate.com/v1/badges/f4fbd03daa49a667d1b7/maintainability)](https://codeclimate.com/github/Furtif/POGOProtos/maintainability) [![Test Coverage](https://api.codeclimate.com/v1/badges/f4fbd03daa49a667d1b7/test_coverage)](https://codeclimate.com/github/Furtif/POGOProtos/test_coverage)-->
=========

![alt text][1.1] <strong><em>`The contents of this repo are a proof of concept and are for educational use only`</em></strong>![alt text][1.1]<br/>

---

This repository contains the [ProtoBuf](https://github.com/google/protobuf) `.proto` files needed to decode the PokémonGo RPC.

---

### Versioning
We are following [semantic versioning](http://semver.org/) for POGOProtos.  Every version will be mapped to their current PokémonGo version.

| Version      | Base                                                                                                      | Notes                  | Extra                           |
|--------------|-----------------------------------------------------------------------------------------------------------|------------------------|---------------------------------|
| [2.54.1](https://github.com/Furtif/POGOProtos/raw/master/.current-version)       |  [v0.205.0](https://github.com/Furtif/POGOProtos/blob/master/base/v0.205.0.proto)                         | **Updated** (_[/base/base.proto](https://github.com/Furtif/POGOProtos/blob/master/base/base.proto)_)  |  Protocol Buffers v3.15.8     |

### Addons

| Additional resources as *.json files | Source                                                                               | Status
|------------------------|--------------------------------------------------------------------------------------|--------
| [v2_GAME_MASTER.json](https://raw.githubusercontent.com/Furtif/POGOProtos/master/GM/v2_GAME_MASTER.json) | [Root](https://github.com/Furtif/POGOProtos/tree/master/GM)                                   |  OK
| [GAME_MASTER.json](https://raw.githubusercontent.com/Furtif/POGOProtos/master/GM/GAME_MASTER.json) | [Root](https://github.com/Furtif/POGOProtos/tree/master/GM)                                   |  OK
| [ASSET_DIGEST.json](https://raw.githubusercontent.com/Furtif/POGOProtos/master/GM/ASSET_DIGEST.json) | [Root](https://github.com/Furtif/POGOProtos/tree/master/GM)                                   |  OK

| Additional resources as *.txt files (_[Decode mode by script](https://github.com/Furtif/POGOProtos#decode-game-master-or-asset-digest)_)| Source                                                                               | Status
|------------------------|--------------------------------------------------------------------------------------|--------
| [v2_GAME_MASTER.txt](https://raw.githubusercontent.com/Furtif/POGOProtos/master/GM/v2_GAME_MASTER.txt) | [Root](https://github.com/Furtif/POGOProtos/tree/master/GM)                                   |  OK
| [ASSET_DIGEST.txt](https://raw.githubusercontent.com/Furtif/POGOProtos/master/GM/ASSET_DIGEST.txt) | [Root](https://github.com/Furtif/POGOProtos/tree/master/GM)                                   |  OK

| Additional resources as *.xml files | Source                                                                               | Status
|------------------------|--------------------------------------------------------------------------------------|--------
| [v2_GAME_MASTER.xml](https://raw.githubusercontent.com/Furtif/POGOProtos/master/GM/v2_GAME_MASTER.xml) | [Root](https://github.com/Furtif/POGOProtos/tree/master/GM)                                   |  OK

### Usage
If you want to figure out the current version in an automated system, use this file.
[.current-version](https://github.com/Furtif/POGOProtos/raw/master/.current-version)
*Note: This file will contain pre-release versions too.*

```
usage: compile_base.py [-h] [-gm GENERATE_GAME_MASTER]
                       [-ga GENERATE_ASSET_DIGEST] [-l LANG] [-v VERSION]
                       [-o OUT_PATH] [-m] [-g] [-b] [-k] [-gf]

optional arguments:
  -h, --help            show this help message and exit
  -gm GENERATE_GAME_MASTER, --generate_game_master GENERATE_GAME_MASTER
                        Generates v2_GAME_MASTER.txt form GENERATE_GAME_MASTER
                        = PATH/MY_BINARY.
  -ga GENERATE_ASSET_DIGEST, --generate_asset_digest GENERATE_ASSET_DIGEST
                        Generates ASSET_DIGEST.txt form GENERATE_ASSET_DIGEST
                        = PATH/MY_BINARY.
  -l LANG, --lang LANG  Language to produce proto single file.
  -v VERSION, --version VERSION
                        Set version out ex:. (0.205.0)
  -o OUT_PATH, --out_path OUT_PATH
                        Output path for proto single file.
  -m, --java_multiple_files
                        Write each message to a separate .java file.
  -g, --generate_only   Generates only proto compilable.
  -b, --generate_new_base
                        Generates new proto base refs.
  -k, --keep_proto_file
                        Do not remove .proto file after compiling.
  -gf, --generate_proto_files
                        Generates base/last_files/*.proto.
                        
```

### Preparation
Current recommended protoc version: "Protocol Buffers v3.15.8".
You can find download links [here](https://github.com/google/protobuf/releases).

#### Windows
Be sure to add `protoc` to your environmental path.

#### *nix
Ensure that you have the newest version of `protoc` installed.

#### OS X
Use `homebrew` to install `protobuf ` with `brew install --devel protobuf`.

### Compilation
The compilation creates output specifically for the target language, i.e. respecting naming conventions, etc.  
This is an example of how the generated code will be organized:

##### Compile vx.xxx.x.proto [depending on the version chosen](https://github.com/Furtif/POGOProtos/blob/master/compile_base.py#L12)

 * _Note: the *.desc file is auto created in this function_

```
python compile_base.py -l cpp -k:
 - vx.xxx.x.proto -> out/single_file/cpp/POGOProtos.Rpc.desc
 -                -> out/single_file/cpp/POGOProtos.Rpc.pb.cc
 -                -> out/single_file/cpp/POGOProtos.Rpc.pb.h
 -                -> out/single_file/cpp/POGOProtos.Rpc.proto
```

##### Same similar outputs up but others langs:

```
  python compile_base.py -l csharp -k
  python compile_base.py -l java -k
  python compile_base.py -l js -k
  python compile_base.py -l python -k
  python compile_base.py -l php -k
  python compile_base.py -l objc -k
  python compile_base.py -l ruby -k
  * python compile_base.py -l swift -k
  * python compile_base.py -l go -k
  * python compile_base.py -l lua -k
  * python compile_base.py -l dart -k
```

_* = Needs plugins_

##### Decode Game Master or Asset Digest:

```
  python compile_base.py -gm [./BIN] (as txt)
  python compile_base.py -ga [./BIN] (as txt)
```
---

### Initial [UpStream](https://github.com/Furtif/POGOProtos/tree/upstream)
- [AeonLucid](https://github.com/AeonLucid/POGOProtos)
