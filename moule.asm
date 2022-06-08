extern printf, atoi, malloc
global main
section .data
fmt_int: db "%d", 10, 0
fmt_float: db "%lf", 10, 0
VAR_DECL

section .text
main:
  push rbp
  mov rbp, rsp
  push rdi
  push rsi

VAR_INIT
BODY
RETURN

  add rsp, 16
  pop rbp
  ret
