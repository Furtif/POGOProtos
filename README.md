<!-- define variables -->
[1.1]: http://i.imgur.com/M4fJ65n.png (ATTENTION)

POGOProtos [![Build Status](https://travis-ci.org/Furtif/POGOProtos.svg?branch=master)](https://travis-ci.org/Furtif/POGOProtos) [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.me/rocketbot) [![Maintainability](https://api.codeclimate.com/v1/badges/f4fbd03daa49a667d1b7/maintainability)](https://codeclimate.com/github/Furtif/POGOProtos/maintainability) [![Test Coverage](https://api.codeclimate.com/v1/badges/f4fbd03daa49a667d1b7/test_coverage)](https://codeclimate.com/github/Furtif/POGOProtos/test_coverage)
===================

![alt text][1.1] <strong><em>`The contents of this repo are a proof of concept and are for educational use only`</em></strong>![alt text][1.1]<br/>

This repository contains the [ProtoBuf](https://github.com/google/protobuf) `.proto` files needed to decode the PokémonGo RPC.

### Implemented messages types
 - [``Global``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/RequestType.proto)
 - [``Social``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/Social/SocialAction.proto)
 - [``Platform``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/Platform/PlatformRequestType.proto) 

### Game actions implemented messages types
 - [``GameAccountRegistry``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/Game/GameAccountRegistry/GameAccountRegistryActions.proto)
 - [``GameAnticheat``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/Game/GameAnticheat/GameAnticheatAction.proto)
 - [``GameFitness``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/Game/GameFitness/GameFitnessAction.proto)
 - [``GameGmTemplates``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/Game/GameGmTemplates/GameGmTemplatesAction.proto)
 - [``GameIap``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/Game/GameIap/GameIapAction.proto)
 - [``GameLocationAwareness``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/Game/GameLocationAwareness/GameLocationAwarenessAction.proto)
 - [``GameNotification``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/Game/GameNotification/GameNotificationAction.proto)
 - [``GamePasscode``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/Game/GamePasscode/GamePasscodeAction.proto)
 - [``GamePing``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/Game/GamePing/GamePingAction.proto)
 - [``GamePlayer``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/Game/GamePlayer/GamePlayerAction.proto)
 - [``GamePoi``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/Game/GamePoi/GamePoiAction.proto)
 - [``GamePushNotification``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/Game/GamePushNotification/GamePushNotificationAction.proto)
 - [``GameSocial``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/Game/GameSocial/GameSocialAction.proto)
 - [``GameTelemetry``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/Game/GameTelemetry/GameTelemetryAction.proto)
 - [``GameWebToken``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/Game/GameWebToken/GameWebTokenAction.proto)
   
### Titan Vasa (![alt text][1.1] ??? ![alt text][1.1])
 - [``Titan``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/Titan)
 - [``Vasa``](https://github.com/Furtif/POGOProtos/blob/master/src/POGOProtos/Networking/Requests/Vasa/VasaClientAction.proto#L5)

### Versioning
We are following [semantic versioning](http://semver.org/) for POGOProtos.  Every version will be mapped to their current PokémonGo version.

| Version      | API           | Notes           | Extra                           |
|--------------|---------------|-----------------|---------------------------------|
| 2.51.5       | 0.177.1       | Compatible      |  Protocol Buffers v3.12.3       |

### Usage
If you want to figure out the current version in an automated system, use this file.
[.current-version](https://github.com/Furtif/POGOProtos/raw/master/.current-version)
*Note: This file will contain pre-release versions too.*

### Preparation
Current recommended protoc version: "Protocol Buffers v3.12.3".
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

```
python compile.py js:
 - POGOProtos/Data/PlayerData.proto -> pogoprotos/data/playerdata_pb.js
```

```
python compile.py java [javanano] [--java_multiple_files]:
 - POGOProtos/Data/PlayerData.proto -> POGOProtos/Data/PlayerData.*
```

```
python compile.py php:
 - POGOProtos/Data/PlayerData.proto -> GPBMetadata/POGOProtos/Data/PlayerData.php
 - POGOProtos/Data/PlayerData.proto -> POGOProtos/Data/PlayerData.php
```

```
python compile.py cpp:
 - POGOProtos/Data/PlayerData.proto -> POGOProtos/Data/PlayerData.pb.cpp
```

```
python compile.py csharp:
 - POGOProtos/Data/PlayerData.proto -> POGOProtos/Data/PlayerData.g.cs
```

```
python compile.py objc:
 - POGOProtos/Data/PlayerData.proto -> POGOProtos/Data/PlayerData.pbobjc.m
```

```
python compile.py python:
 - POGOProtos/Data/*.proto -> pogoprotos/data/__init__.py
 - POGOProtos/Data/PlayerData.proto -> pogoprotos/data/player_data_pb2.py
```

```
python compile.py ruby:
 - POGOProtos/Data/*.proto -> pogoprotos/data.rb
 - POGOProtos/Data/PlayerData.proto -> pogoprotos/data/player_data.rb
``` 

#### ![alt text][1.1] Needs plugins ![alt text][1.1]
```
python compile.py swift:
 - POGOProtos/Data/PlayerData.proto -> POGOProtos/Data/PlayerData.pb.swift
```

```
python compile.py lua:
 - POGOProtos/Data/PlayerData.proto -> POGOProtos/Data/PlayerData_pb.lua
```

```
python compile.py go:
 - POGOProtos/Data/*.proto -> github.com/aeonlucid/pogoprotos/data
 - POGOProtos/Data/PlayerData.proto -> github.com/aeonlucid/pogoprotos/data/player_data.pb.go
```

```
python compile.py dart:
 - POGOProtos/Data/PlayerData.proto -> *.*
```

```
python compile.py rust:
 - POGOProtos/Data/PlayerData.proto -> POGOProtos/Data/PlayerData.rs
```

### Extra information
 - Run ```python compile.py --help``` for help.
 - You can find all available languages here [https://github.com/google/protobuf](https://github.com/google/protobuf).
 
### Libraries
If you don't want to compile POGOProtos but instead use it directly, check out the following repository.

| Additional resources  | Source                                                                               | Status 
|-----------------------|--------------------------------------------------------------------------------------|--------
| Gamemaster Json       | https://github.com/pokemongo-dev-contrib/pokemongo-game-master                       |  OK    

### CREDITS
 - [AeonLucid](https://github.com/AeonLucid)
