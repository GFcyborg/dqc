# DQC (Distributed Quantum Computing)

[This project](https://github.com/GFcyborg/dqc) is a language+compiler written in Java, aimed at splitting monolithic quantum circuits (written in OpenQASM 3.0) into a pool of cooperating sub-programs/chuncks (written in OpenQASM as well) to be run on a distributed **network of QPUs**, hopefully acting together as a choreography by sharing quantum data (qubits) via [**quantum teleportation**](https://en.wikipedia.org/wiki/Quantum_network) (i.e. consuming ebits), while classical binary data (bits & Bytes) get shared the usual way (e.g. TCP/IP). The main challenges of this project are:

* finding and marking the best split points (possibly optimizing for minimum ebit usage);
* finding the working set of a given split point (i.e. data to be passed to the next chunck);
* injecting teleportations at both sides of each split point;
* overall sync among chunks (do we need a flat architecture or a controller/worker hierarchy?)
* [optional] QPU allocation

This work started in Dec. 2025 as my MSc. thesis on [Quantum Computing](https://www.sdu.dk/en/qm) at the [**SDU.dk** - Southern Denmark University / IMADA dept](https://www.sdu.dk/en/om-sdu/institutter-centre/imada_matematik_og_datalogi).


## :bangbang: Latest News :bangbang:

None, so far.


## Quick Start Guide

The code is supposed to automatically generate a lot of artifacts (both binary and auto-generated code) by using **Gradle 9+** and **Antlr4**. Provided that you already have all [**requirements**](#requirements) in place, run the following command from the project root-directory (where settings.gradle is located, **NOT** from the ./app/ folder) in order to do the build:

**./gradlew clean build test run --warning-mode all**

e.g.:

```text
gf@ant:~/.../dqc$ ./gradlew clean build test run --warning-mode all
Reusing configuration cache.

> Task :app:run
Parsed successfully: 
(program (version OPENQASM 3.0 ;) (statementOrScope (statement (quantumDeclarationStatement (qubitType qubit) q ;))) <EOF>)

BUILD SUCCESSFUL in 4s
8 actionable tasks: 8 executed
Configuration cache entry reused.
```

### Requirements
To install an updated version of gradle, first install any system-wide gradle version (usually out-of-date), and then use it to locally install an up-to-date wrapper to the top-level dir of this project:

```text
gf@ant:~$ sudo apt install gradle
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
gradle is already the newest version (4.4.1-20).
0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.

gf@ant:~$ cd ~/.../dqc
gf@ant:~/.../dqc$ gradle wrapper --gradle-version 9.2.1
...

$ cat /usr/bin/antlr4
#!/bin/sh
## GF: removed the wrong trailing extra backslash from (...antlr3-runtime.jar/:)
CLASSPATH=/usr/share/java/stringtemplate4.jar:/usr/share/java/antlr4.jar:/usr/share/java/
antlr4-runtime.jar:/usr/share/java/antlr3-runtime.jar:/usr/share/java/treelayout.jar
exec java -cp $CLASSPATH org.antlr.v4.Tool "$@"

$ wget https://www.antlr.org/download/antlr-4.13.2-complete.jar
# mv antlr-4.13.2-complete.jar /usr/share/java/antlr4.jar

$ ll /usr/share/java/antlr4*
... 2140045 Dec 8 16:00 /usr/share/java/antlr4-4.13.2-complete.jar
... /usr/share/java/antlr4.jar -> antlr4-4.13.2-complete.jar
... 326307 Dec 17 18:23 /usr/share/java/antlr4-runtime-4.13.2.jar
... /usr/share/java/antlr4-runtime.jar -> antlr4-runtime-4.13.2.jar

$ java org.antlr.v4.Tool # same as: java -jar /usr/share/java/antlr4.jar
ANTLR Parser Generator Version 4.13.2
...
```


### Environment

My current setup (just for reference) is:

```text
gf@ant:~/.../dqc$ neofetch 
             ...-:::::-...                 gf@ant 
          .-MMMMMMMMMMMMMMM-.              ------ 
      .-MMMM`..-:::::::-..`MMMM-.          OS: Linux Mint 22.3 x86_64 
    .:MMMM.:MMMMMMMMMMMMMMM:.MMMM:.        Host: 20JNS24C00 ThinkPad T470 W10DG 
   -MMM-M---MMMMMMMMMMMMMMMMMMM.MMM-       Kernel: 6.14.0-37-generic 
 `:MMM:MM`  :MMMM:....::-...-MMMM:MMM:`    Uptime: 1 day, 1 hour, 14 mins 
 :MMM:MMM`  :MM:`  ``    ``  `:MMM:MMM:    Packages: 4167 (dpkg), 32 (flatpak), 13 (snap) 
.MMM.MMMM`  :MM.  -MM.  .MM-  `MMMM.MMM.   Shell: bash 5.2.21 
:MMM:MMMM`  :MM.  -MM-  .MM:  `MMMM-MMM:   Resolution: 1920x1080 
:MMM:MMMM`  :MM.  -MM-  .MM:  `MMMM:MMM:   DE: Cinnamon 6.6.6 
:MMM:MMMM`  :MM.  -MM-  .MM:  `MMMM-MMM:   WM: Mutter (Muffin) 
.MMM.MMMM`  :MM:--:MM:--:MM:  `MMMM.MMM.   WM Theme: Mint-Y-Dark (Mint-Y) 
 :MMM:MMM-  `-MMMMMMMMMMMM-`  -MMM-MMM:    Theme: Mint-Y-Aqua [GTK2/3] 
  :MMM:MMM:`                `:MMM:MMM:     Icons: Mint-Y-Sand [GTK2/3] 
   .MMM.MMMM:--------------:MMMM.MMM.      Terminal: terminator 
     '-MMMM.-MMMMMMMMMMMMMMM-.MMMM-'       CPU: Intel i5-6300U (4) @ 3.000GHz 
       '.-MMMM``--:::::--``MMMM-.'         GPU: Intel Skylake GT2 [HD Graphics 520] 
            '-MMMMMMMMMMMMM-'              Memory: 6512MiB / 31845MiB 
               ``-:::::-``

gf@ant:~/.../dqc$ ./gradlew -v

------------------------------------------------------------
Gradle 9.2.1
------------------------------------------------------------

Build time:    2025-11-17 13:40:48 UTC
Revision:      30ecdc708db275e8f8769ea0620f6dd919a58f76

Kotlin:        2.2.20
Groovy:        4.0.28
Ant:           Apache Ant(TM) version 1.10.15 compiled on August 25 2024
Launcher JVM:  21.0.9 (Ubuntu 21.0.9+10-Ubuntu-124.04)
Daemon JVM:    /usr/lib/jvm/java-21-openjdk-amd64 (no JDK specified, using current Java home)
OS:            Linux 6.14.0-37-generic amd64

gf@ant:~/.../dqc$ antlr4 
* original CLASSPATH=.:/usr/share/java/antlr4.jar:/usr/share/java/antlr4-runtime.jar:
* modified CLASSPATH=/usr/share/java/stringtemplate4.jar:/usr/share/java/antlr4.jar:/usr/share/java/antlr4-runtime.jar:/usr/share/java/antlr3-runtime.jar:/usr/share/java/treelayout.jar

ANTLR Parser Generator  Version 4.13.2
...

gf@ant:~$ code -v
1.108.2
c9d77990917f3102ada88be140d28b038d1dd7c7
x64

gf@ant:~$ /snap/intellij-idea-ultimate/current/bin/idea --version
IntelliJ IDEA 2025.3.2
Build #IU-253.30387.90

gf@ant:~$ cursor -v
2.4.21
dc8361355d709f306d5159635a677a571b277bc0
x64

```


## Citations

This work has taken much inspiration and help from:

* Terence Parr [ANTLR4](https://www.antlr.org/download) 2024, [git repo](https://github.com/antlr/antlr4/blob/master/doc/getting-started.md) 2025;

* Gabriele Tomassetti [The ANTLR Mega Tutorial](https://tomassetti.me/antlr-mega-tutorial/), 2017;

* OpenQASM grammars (\*.g4) from [git repo](https://github.com/openqasm/openqasm/tree/main/source/grammar), 2025;

* coding assistant AI's: ChatGPT, Copilot, Gemini, Claude


## Contacts

To avoid spam bots, these email addresses must be fixed manually ( \_at\_ = @):

* Giacomo Fagioli at [**gifag24_at_student.sdu.dk**](mailto:gifag24_at_student.sdu.dk), or private1 [giacomofagioli_at_gmail.com](mailto:giacomofagioli_at_gmail.com), or private2 [gf_at_gfcyb.org](mailto:gf_at_gfcyb.org)
* My **SDU** supervisors: Prof. [Robin Kaarsgaard](https://www.sdu.dk/en/forskning/qm/employees/vip-staff/robin-kaarsgaard-sales), Prof. [Marco Peressotti](https://portal.findresearcher.sdu.dk/en/persons/peressotti/)
