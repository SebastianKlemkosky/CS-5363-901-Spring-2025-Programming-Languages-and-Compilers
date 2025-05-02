	# standard Decaf preamble 
	  .text
	  .align 2
	  .globl main
  _Pi:
    # BeginFunc 0
	  subu $sp, $sp, 8  # decrement sp to make space to save ra, fp
	  sw $fp, 8($sp)    # save fp
	  sw $ra, 4($sp)    # save ra
	  addiu $fp, $sp, 8 # set up new fp
	  subu $sp, $sp, 0 # decrement sp to make space for locals/temps
    # EndFunc
    # (below handles reaching end of fn body with no explicit return)
	  move $sp, $fp     # pop callee frame off stack
	  lw $ra, -4($fp)   # restore saved ra
	  lw $fp, 0($fp)    # restore saved fp
	  jr $ra        # return from function
  _Multiply:
    # BeginFunc 4
	  subu $sp, $sp, 8  # decrement sp to make space to save ra, fp
	  sw $fp, 8($sp)    # save fp
	  sw $ra, 4($sp)    # save ra
	  addiu $fp, $sp, 8 # set up new fp
	  subu $sp, $sp, 4 # decrement sp to make space for locals/temps
	# _tmp0 = x * y
	  lw $t0, 4($fp)	# fill x to $t0 from $fp+4
	  lw $t1, 8($fp)	# fill y to $t1 from $fp+8
	  mul $t2, $t0, $t1
	  sw $t2, -8($fp)	# spill _tmp0 from $t2 to $fp-8
	# Return _tmp0
	  lw $t2, -8($fp)	# fill _tmp0 to $t2 from $fp-8
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
    # BeginFunc 28
	  subu $sp, $sp, 8  # decrement sp to make space to save ra, fp
	  sw $fp, 8($sp)    # save fp
	  sw $ra, 4($sp)    # save ra
	  addiu $fp, $sp, 8 # set up new fp
	  subu $sp, $sp, 28 # decrement sp to make space for locals/temps
	# _tmp1 = LCall _Pi
	  jal _Pi			    # jump to function
	  move $t2, $v0	    # copy function return value from $v0
	  sw $t2, -20($fp)	# spill _tmp1 from $t2 to $fp-20
	# a = _tmp1
	  lw $t2, -20($fp)	# fill _tmp1 to $t2 from $fp-20
	  sw $t2, -8($fp)	# spill a from $t2 to $fp-8
	# _tmp2 = LCall _Multiply
	  jal _Multiply			    # jump to function
	  move $t2, $v0	    # copy function return value from $v0
	  sw $t2, -24($fp)	# spill _tmp2 from $t2 to $fp-24
	# PopParams 8
	  add $sp, $sp, 8	# pop params off stack
	# result = _tmp2
	  lw $t2, -24($fp)	# fill _tmp2 to $t2 from $fp-24
	  sw $t2, -16($fp)	# spill result from $t2 to $fp-16
	# _tmp3 = 1
	  li $t2, 1	# load constant value 1
	  sw $t2, -28($fp)	# spill _tmp3 from $t2 to $fp-28
	# PushParam _tmp3
	  subu $sp, $sp, 4	# decrement sp to make space for param
	  lw $t0, -28($fp)	# fill _tmp3 to $t0 from $fp-28
	  sw $t0, 4($sp)	# copy param value to stack
	# LCall _PrintInt
	  jal _PrintInt        # jump to function
	# PopParams 4
	  add $sp, $sp, 4	# pop params off stack
	# _tmp4 = " done.\n"
	  .data 	    # create string constant marked with label
	  _string1: .asciiz " done.\n"
	  .text
	  la $t2, _string1	# load label
	  sw $t2, -32($fp)	# spill _tmp4 from $t2 to $fp-32
	# PushParam _tmp4
	  subu $sp, $sp, 4	# decrement sp to make space for param
	  lw $t0, -32($fp)	# fill _tmp4 to $t0 from $fp-32
	  sw $t0, 4($sp)	# copy param value to stack
	# LCall _PrintString
	  jal _PrintString      # jump to function
	# PopParams 4
	  add $sp, $sp, 4	# pop params off stack
    # EndFunc
    # (below handles reaching end of fn body with no explicit return)
	  move $sp, $fp     # pop callee frame off stack
	  lw $ra, -4($fp)   # restore saved ra
	  lw $fp, 0($fp)    # restore saved fp
	  jr $ra        # return from function
