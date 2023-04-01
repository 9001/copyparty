#!/bin/bash
set -e

langs=(
    markup
    css
    clike
    javascript
    autohotkey
    bash
    basic
    batch
    c
    csharp
    cpp
    cmake
    diff
    docker
    elixir
    glsl
    go
    ini
    java
    json
    kotlin
    latex
    less
    lisp
    lua
    makefile
    matlab
    moonscript
    nim
    objectivec
    perl
    powershell
    python
    r
    jsx
    ruby
    rust
    sass
    scss
    sql
    swift
    systemd
    toml
    typescript
    vbnet
    verilog
    vhdl
    yaml
    zig
)

slangs="${langs[*]}"
slangs="${slangs// /+}"

for theme in prism-funky prism ; do
    u="https://prismjs.com/download.html#themes=$theme&languages=$slangs&plugins=line-highlight+line-numbers+autolinker"
    echo "$u"
    ./genprism.py --dir prism-$1 --js-out prism.js --css-out $theme.css "$u"
done

mv prism-funky.css prismd.css
mv prismd.css prism.css prism.js /z/dist/
