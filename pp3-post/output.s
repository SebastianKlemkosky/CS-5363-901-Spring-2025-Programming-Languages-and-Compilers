	# standard Decaf preamble 
	  .text
	  .align 2
	  .globl main
  _factorial:
    # BeginFunc 28
	  subu $sp, $sp, 8  # decrement sp to make space to save ra, fp
	  sw $fp, 8($sp)    # save fp
	  sw $ra, 4($sp)    # save ra
	  addiu $fp, $sp, 8 # set up new fp
	  subu $sp, $sp, 28 # decrement sp to make space for locals/temps
	# _tmp0 = 1
	  li $t2, 1	    # load constant value 1 into $t2
	  sw $t2, -8($fp)	# spill _tmp0 from $t2 to $fp-8
	# _tmp1 = n < _tmp0
	  lw $t0, 4($fp)	# fill n to $t0 from $fp+4
	  lw $t1, -8($fp)	# fill _tmp0 to $t1 from $fp-8
	  slt $t2, $t0, $t1
	  sw $t2, -12($fp)	# spill _tmp1 from $t2 to $fp-12
	# _tmp2 = n == _tmp0
	  lw $t0, 4($fp)	# fill n to $t0 from $fp+4
	  lw $t1, -8($fp)	# fill _tmp0 to $t1 from $fp-8
	  seq $t2, $t0, $t1
	  sw $t2, -16($fp)	# spill _tmp2 from $t2 to $fp-16
	# _tmp3 = _tmp1 || _tmp2
	  lw $t0, -12($fp)	# fill _tmp1 to $t0 from $fp-12
	  lw $t1, -16($fp)	# fill _tmp2 to $t1 from $fp-16
	  or $t2, $t0, $t1
	  sw $t2, -20($fp)	# spill _tmp3 from $t2 to $fp-20
	# IfZ _tmp3 Goto _L0
	  lw $t0, -20($fp)	# fill _tmp3
	  beqz $t0, _L0
_L0:
	# _tmp5 = n - 1
	  lw $t0, -4($fp)	# load n
	  li $t1, 1	# load 1
	  sub $t2, $t0, $t1
	  sw $t2, -28($fp)	# spill _tmp5
	# PushParam _tmp5
	  subu $sp, $sp, 4	# decrement sp to make space for param
	  lw $t0, -28($fp)	# fill _tmp5 to $t0 from $fp-28
	  sw $t0, 4($sp)	# copy param value to stack
	# LCall _factorial
	  jal _factorial	     # jump to function
	  move $t2, $v0	# copy return value from $v0
	  add $sp, $sp, 4	# pop params off stack
	  sw $t2, -24($fp)	# store result into _tmp4
	# _tmp6 = n * _tmp4
	  lw $t0, 4($fp)	# fill n to $t0 from $fp+4
	  lw $t1, -24($fp)	# fill _tmp4 to $t1 from $fp+-24
	  mul $t2, $t0, $t1
	  sw $t2, -32($fp)	# spill _tmp6 from $t2 to $fp-32
	# Return _tmp6
	  lw $t2, -32($fp)	# fill _tmp6 to $t2 from $fp-32
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
    # BeginFunc 4
	  subu $sp, $sp, 8  # decrement sp to make space to save ra, fp
	  sw $fp, 8($sp)    # save fp
	  sw $ra, 4($sp)    # save ra
	  addiu $fp, $sp, 8 # set up new fp
	  subu $sp, $sp, 4 # decrement sp to make space for locals/temps
    # EndFunc
    # (below handles reaching end of fn body with no explicit return)
	  move $sp, $fp     # pop callee frame off stack
	  lw $ra, -4($fp)   # restore saved ra
	  lw $fp, 0($fp)    # restore saved fp
	  jr $ra        # return from function
