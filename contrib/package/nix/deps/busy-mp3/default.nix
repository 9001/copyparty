{ runCommand, sox, lame, pigz }: runCommand "busy-mp3"
{
  nativeBuildInputs = [ sox lame pigz ];
}
  ''
    ${builtins.readFile ./../../../../../scripts/deps-docker/busy-mp3.sh}
    mv /dev/shm/busy.mp3.gz $out
  ''
