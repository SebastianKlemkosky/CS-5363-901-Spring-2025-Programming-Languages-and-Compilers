	# standard Decaf preamble 
	  .text
	  .align 2
	  .globl main
  _foo:
    # BeginFunc 16
	  subu $sp, $sp, 8  # decrement sp to make space to save ra, fp
	  sw $fp, 8($sp)    # save fp
	  sw $ra, 4($sp)    # save ra
	  addiu $fp, $sp, 8 # set up new fp
	  subu $sp, $sp, 16 # decrement sp to make space for locals/temps
	# IfZ c Goto _L0
	  lw $t0, 8($fp)	# fill c to $t0 from $fp+8
	  beqz $t0, _L0	# branch if c is zero
	# _tmp0 = 2
	  li $t2, 2	    # load constant value 2 into $t2
	  sw $t2, -8($fp)	# spill _tmp0 from $t2 to $fp-8
	# _tmp1 = a + _tmp0
	  lw $t0, 0($gp)	# fill a to $t0 from $gp+0
	  lw $t1, -8($fp)	# fill _tmp0 to $t1 from $fp-8
	  add $t2, $t0, $t1
	  sw $t2, -12($fp)	# spill _tmp1 from $t2 to $fp-12
	# Return _tmp1
	  lw $t2, -12($fp)	# fill _tmp1 to $t2 from $fp-12
	  move $v0, $t2	# assign return value into $v0
	  move $sp, $fp     # pop callee frame off stack
	  lw $ra, -4($fp)   # restore saved ra
	  lw $fp, 0($fp)    # restore saved fp
	  jr $ra        # return from function
    # Goto _L1
	  b _L1	    # unconditional branch
  _L0:
	# PushParam a
	  subu $sp, $sp, 4	# decrement sp to make space for param
	  lw $t0, 4($fp)	# fill a to $t0 from $fp+4
	  sw $t0, 4($sp)	# copy param value to stack
	# LCall _PrintInt
	  jal _PrintInt        # jump to function
	# PopParams 4
	  add $sp, $sp, 4	# pop params off stack
	# _tmp2 = " wacky.\n"
	  .data 	    # create string constant marked with label
	  _string1: .asciiz " wacky.\n"
	  .text
	  la $t2, _string1	# load label
	  sw $t2, -16($fp)	# spill _tmp2 from $t2 to $fp-16
	# PushParam _tmp2
	  subu $sp, $sp, 4	# decrement sp to make space for param
	  lw $t0, -16($fp)	# fill _tmp2 to $t0 from $fp-16
	  sw $t0, 4($sp)	# copy param value to stack
	# LCall _PrintString
	  jal _PrintString      # jump to function
	# PopParams 4
	  add $sp, $sp, 4	# pop params off stack
  _L1:
	# _tmp3 = 18
	  li $t2, 18	    # load constant value 18 into $t2
	  sw $t2, -20($fp)	# spill _tmp3 from $t2 to $fp-20
	# Return _tmp3
	  lw $t2, -20($fp)	# fill _tmp3 to $t2 from $fp-20
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
    # BeginFunc 80
	  subu $sp, $sp, 8  # decrement sp to make space to save ra, fp
	  sw $fp, 8($sp)    # save fp
	  sw $ra, 4($sp)    # save ra
	  addiu $fp, $sp, 8 # set up new fp
	  subu $sp, $sp, 80 # decrement sp to make space for locals/temps
	# _tmp4 = 10
	  li $t2, 10	    # load constant value 10 into $t2
	  sw $t2, -12($fp)	# spill _tmp4 from $t2 to $fp-12
	# a = _tmp4
	  lw $t2, -12($fp)	# fill _tmp4 to $t2 from $fp-12
	  sw $t2, 0($gp)	# spill a from $t2 to $gp+0
	# _tmp5 = 2
	  li $t2, 2	    # load constant value 2 into $t2
	  sw $t2, -16($fp)	# spill _tmp5 from $t2 to $fp-16
	# _tmp6 = a / _tmp5
	  lw $t0, 0($gp)	# fill a to $t0 from $gp+0
	  lw $t1, -16($fp)	# fill _tmp5 to $t1 from $fp-16
	  div $t2, $t0, $t1
	  sw $t2, -20($fp)	# spill _tmp6 from $t2 to $fp-20
	# b = _tmp6
	  lw $t2, -20($fp)	# fill _tmp6 to $t2 from $fp-20
	  sw $t2, -8($fp)	# spill b from $t2 to $fp-8
	# _tmp7 = 1
	  li $t2, 1	    # load constant value 1 into $t2
	  sw $t2, -24($fp)	# spill _tmp7 from $t2 to $fp-24
	  subu $sp, $sp, 4	# decrement sp to make space for param
	  lw $t0, -24($fp)	# fill _tmp7 to $t0 from $fp-24
	  sw $t0, 4($sp)	# copy param value to stack
	# PushParam a
	  subu $sp, $sp, 4	# decrement sp to make space for param
	  lw $t0, 0($gp)	# fill a to $t0 from $gp+0
	  sw $t0, 4($sp)	# copy param value to stack
	# _tmp8 = LCall _foo
	  jal _foo	    # jump to function
	  move $t2, $v0	    # copy function return value from $v0
	  sw $t2, -28($fp)	# spill _tmp8 from $t2 to $fp-28
	# PopParams 8
	  add $sp, $sp, 8	# pop params off stack
	# _tmp9 = a < b
	  lw $t0, 4($fp)	# fill a to $t0 from $fp+4
	  lw $t1, -8($fp)	# fill b to $t1 from $fp-8
	  slt $t2, $t0, $t1
	  sw $t2, -32($fp)	# spill _tmp9 from $t2 to $fp-32
	# _tmp10 = a == b
	  lw $t0, 4($fp)	# fill a to $t0 from $fp+4
	  lw $t1, -8($fp)	# fill b to $t1 from $fp-8
	  seq $t2, $t0, $t1
	  sw $t2, -36($fp)	# spill _tmp10 from $t2 to $fp-36
	# _tmp11 = _tmp9 || _tmp10
	  lw $t0, -32($fp)	# fill _tmp9 to $t0 from $fp-32
	  lw $t1, -36($fp)	# fill _tmp10 to $t1 from $fp-36
	  or $t2, $t0, $t1
	  sw $t2, -40($fp)	# spill _tmp11 from $t2 to $fp-40
	# PushParam _tmp11
	  subu $sp, $sp, 4	# decrement sp to make space for param
	  lw $t0, -40($fp)	# fill _tmp11 to $t0 from $fp-40
	  sw $t0, 4($sp)	# copy param value to stack
	# _tmp12 = 2
	  li $t2, 2	    # load constant value 2 into $t2
	  sw $t2, -44($fp)	# spill _tmp12 from $t2 to $fp-44
	# _tmp13 = b + _tmp12
	  lw $t0, -8($fp)	# fill b to $t0 from $fp-8
	  lw $t1, -44($fp)	# fill _tmp12 to $t1 from $fp-44
	  add $t2, $t0, $t1
	  sw $t2, -48($fp)	# spill _tmp13 from $t2 to $fp-48
	# PushParam _tmp13
	  subu $sp, $sp, 4	# decrement sp to make space for param
	  lw $t0, -48($fp)	# fill _tmp13 to $t0 from $fp-48
	  sw $t0, 4($sp)	# copy param value to stack
	# _tmp14 = LCall _foo
	  jal _foo	    # jump to function
	  move $t2, $v0	    # copy function return value from $v0
	  sw $t2, -52($fp)	# spill _tmp14 from $t2 to $fp-52
	# PopParams 8
	  add $sp, $sp, 8	# pop params off stack
	# _tmp15 = 1
	  li $t2, 1
	  sw $t2, -56($fp)	# spill _tmp15
	# _tmp16 = !_tmp15
	  lw $t0, -56($fp)
	  seqz $t2, $t0	# NOT operation
	  sw $t2, -60($fp)	# spill _tmp16
	# PushParam _tmp16
	  subu $sp, $sp, 4	# decrement sp to make space for param
	  lw $t0, -60($fp)	# fill _tmp16 to $t0 from $fp-60
	  sw $t0, 4($sp)	# copy param value to stack
	# _tmp17 = 0
	  li $t2, 0
	  sw $t2, -64($fp)	# spill _tmp17
	# _tmp18 = 1
	  li $t2, 1
	  sw $t2, -68($fp)	# spill _tmp18
	# _tmp19 = _tmp18 && _tmp17
	  lw $t0, -68($fp)
	  lw $t1, -64($fp)
	  and $t2, $t0, $t1
	  sw $t2, -72($fp)	# spill _tmp19
	# PushParam _tmp19
	  subu $sp, $sp, 4	# decrement sp to make space for param
	  lw $t0, -72($fp)	# fill _tmp19 to $t0 from $fp-72
	  sw $t0, 4($sp)	# copy param value to stack
	# _tmp20 = 3
	  li $t2, 3	# load const 3
	  sw $t2, -76($fp)	# spill _tmp20 from $t2 to $fp-76
	  subu $sp, $sp, 4	# decrement sp to make space for param
	  lw $t0, -76($fp)	# fill _tmp20 to $t0 from $fp-76
	  sw $t0, 4($sp)	# copy param value to stack
	# _tmp21 = LCall _foo
	  jal _foo	    # jump to function
	  move $t2, $v0	    # copy function return value from $v0
	  sw $t2, -80($fp)	# spill _tmp21 from $t2 to $fp-80
	# PopParams 8
	  add $sp, $sp, 8	# pop params off stack
	# PushParam _tmp21
	  subu $sp, $sp, 4	# decrement sp to make space for param
	  lw $t0, -80($fp)	# fill _tmp21 to $t0 from $fp-80
	  sw $t0, 4($sp)	# copy param value to stack
	# _tmp22 = LCall _foo
	  jal _foo	    # jump to function
	  move $t2, $v0	    # copy function return value from $v0
	  sw $t2, -84($fp)	# spill _tmp22 from $t2 to $fp-84
	# PopParams 8
	  add $sp, $sp, 8	# pop params off stack
    # EndFunc
    # (below handles reaching end of fn body with no explicit return)
	  move $sp, $fp     # pop callee frame off stack
	  lw $ra, -4($fp)   # restore saved ra
	  lw $fp, 0($fp)    # restore saved fp
	  jr $ra        # return from function
