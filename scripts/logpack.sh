#!/bin/bash
set -e

# recompress logs so they decompress faster + save some space;
# * will not recurse into subfolders
# * each file in current folder gets recompressed to zstd; input file is DELETED
# * any xz-compressed logfiles are decompressed before converting to zstd
# * SHOULD ignore and skip files which are currently open; SHOULD be safe to run while copyparty is running


# for files larger than $cutoff, compress with `zstd -T0`
# (otherwise do several files in parallel (scales better))
cutoff=400M


# osx support:
# port install findutils gsed coreutils
command -v gfind >/dev/null &&
command -v gsed  >/dev/null &&
command -v gsort >/dev/null && {
    find() { gfind "$@"; }
    sed()  { gsed  "$@"; }
    sort() { gsort "$@"; }
}

packfun() {
    local jobs=$1 fn="$2"
    printf '%s\n' "$fn" | grep -qF .zst && return

    local of="$(printf '%s\n' "$fn" | sed -r 's/\.(xz|txt)/.zst/')"
    [ "$fn" = "$of" ] &&
        of="$of.zst"

    [ -e "$of" ] &&
        echo "SKIP: output file exists: $of" &&
        return

    lsof -- "$fn" 2>/dev/null | grep -E .. &&
        printf "SKIP: file in use: %s\n\n" $fn &&
        return

    # determine by header; old copyparty versions would produce xz output without .xz names
    head -c3 "$fn" | grep -qF 7z &&
        cmd="xz -dkc" || cmd="cat"

    printf '<%s> T%d: %s\n' "$cmd" $jobs "$of"

    $cmd <"$fn" >/dev/null || {
        echo "ERROR: uncompress failed: $fn"
        return
    }

    $cmd <"$fn" | zstd --long -19 -T$jobs >"$of"
    touch -r "$fn" -- "$of"

    cmp <($cmd <"$fn") <(zstd -d <"$of") || {
        echo "ERROR: data mismatch: $of"
        mv "$of"{,.BAD}
        return
    }
    rm -- "$fn"
}

# do small files in parallel first (in descending size);
# each file can use 4 threads in case the cutoff is poor
export -f packfun
export -f sed 2>/dev/null || true
find -maxdepth 1 -type f -size -$cutoff -printf '%s %p\n' |
sort -nr | sed -r 's`[^ ]+ ``; s`^\./``' | tr '\n' '\0' |
xargs "$@" -0i -P$(nproc) bash -c 'packfun 4 "$@"' _ {}

# then the big ones, letting each file use the whole cpu
for f in *; do packfun 0 "$f"; done
