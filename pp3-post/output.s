	# standard Decaf preamble 
	  .text
	  .align 2
	  .globl main
  _foo:
    # BeginFunc 12
	  subu $sp, $sp, 8  # decrement sp to make space to save ra, fp
	  sw $fp, 8($sp)    # save fp
	  sw $ra, 4($sp)    # save ra
	  addiu $fp, $sp, 8 # set up new fp
	  subu $sp, $sp, 12 # decrement sp to make space for locals/temps
	# IfZ c Goto _L0
	  lw $t0, 8($fp)	# fill c to $t0 from $fp+8
	  beqz $t0, _L0	# branch if c is zero
	# _tmp0 = a + 2
	  lw $t0, 4($fp)	# fill a to $t0 from $fp+4
	  li $t1, 2	# load const 2 into $t1
	  add $t2, $t0, $t1
	  sw $t2, -8($fp)	# spill _tmp0 from $t2 to $fp-8
	# Return _tmp0
	  lw $t2, -8($fp)	# fill _tmp0 to $t2 from $fp-8
	  move $v0, $t2	    # assign return value into $v0
	  move $sp, $fp     # pop callee frame off stack
	  lw $ra, -4($fp)   # restore saved ra
	  lw $fp, 0($fp)    # restore saved fp
	  jr $ra        # return from function
	  j _L1
  _L0:
	# PushParam a
	  subu $sp, $sp, 4	# decrement sp to make space for param
	  lw $t0, 4($fp)	# fill a to $t0 from $fp4
	  sw $t0, 4($sp)	# copy param value to stack
	# LCall _PrintInt
	  jal _PrintInt        # jump to function
	# PopParams 4
	  add $sp, $sp, 4	# pop params off stack
	# _tmp1 = " wacky.\n"
	  .data 	    # create string constant marked with label
	  _string1: .asciiz " wacky.\n"
	  .text
	  la $t2, _string1	# load label
	  sw $t2, -12($fp)	# spill _tmp1 from $t2 to $fp-12
	# PushParam _tmp1
	  subu $sp, $sp, 4	# decrement sp to make space for param
	  lw $t0, -12($fp)	# fill _tmp1 to $t0 from $fp-12
	  sw $t0, 4($sp)	# copy param value to stack
	# LCall _PrintString
	  jal _PrintString      # jump to function
	# PopParams 4
	  add $sp, $sp, 4	# pop params off stack
_L1:
	# _tmp2 = 18
	  li $t2, 18	    # load constant value 18 into $t2
	  sw $t2, -16($fp)	# spill _tmp2 from $t2 to $fp-16
	# Return _tmp2
	  lw $t2, -16($fp)	# fill _tmp2 to $t2 from $fp-16
	  move $v0, $t2	    # assign return value into $v0
	  move $sp, $fp     # pop callee frame off stack
	  lw $ra, -4($fp)   # restore saved ra
	  lw $fp, 0($fp)    # restore saved fp
	  jr $ra        # return from function
    # EndFunc
    # (below handles reaching end of fn body with no explicit return)
	  move $sp, $fp     # pop callee frame off stack
	  lw $ra, -4($fp)   # restore saved ra
	  lw $fp, 0($fp)    # restore saved fp
	  jr $ra        # return from function
  main:
    # BeginFunc 16
	  subu $sp, $sp, 8  # decrement sp to make space to save ra, fp
	  sw $fp, 8($sp)    # save fp
	  sw $ra, 4($sp)    # save ra
	  addiu $fp, $sp, 8 # set up new fp
	  subu $sp, $sp, 16 # decrement sp to make space for locals/temps
	# _tmp3 = 10
	  li $t2, 10	    # load constant value 10 into $t2
	  sw $t2, -12($fp)	# spill _tmp3 from $t2 to $fp-12
	# a = _tmp3
	  lw $t2, -12($fp)	# fill _tmp3 to $t2 from $fp-12
	  sw $t2, -4($fp)	# spill a from $t2 to $fp-4
	# _tmp4 = 2
	  li $t2, 2	    # load constant value 2 into $t2
	  sw $t2, -16($fp)	# spill _tmp4 from $t2 to $fp-16
	# _tmp5 = a / _tmp4
	  lw $t0, 4($fp)	# fill a to $t0 from $fp+4
	  lw $t1, -16($fp)	# fill _tmp4 to $t1 from $fp-16
	  div $t2, $t0, $t1
	  sw $t2, -20($fp)	# spill _tmp5 from $t2 to $fp-20
	# b = _tmp5
	  lw $t2, -20($fp)	# fill _tmp5 to $t2 from $fp-20
	  sw $t2, -8($fp)	# spill b from $t2 to $fp-8
    # EndFunc
    # (below handles reaching end of fn body with no explicit return)
	  move $sp, $fp     # pop callee frame off stack
	  lw $ra, -4($fp)   # restore saved ra
	  lw $fp, 0($fp)    # restore saved fp
	  jr $ra        # return from function
