python3 compilo.py > hum.asm
nasm -felf64 hum.asm
gcc -no-pie -fno-pie hum.o
./a.out $1 $2 $3 $4 $5 $6 $7 $8 $9