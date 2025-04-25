	# standard Decaf preamble 
	  .text
	  .align 2
	  .globl main
  _factorial:
    # BeginFunc 12
	  subu $sp, $sp, 8  # decrement sp to make space to save ra, fp
	  sw $fp, 8($sp)    # save fp
	  sw $ra, 4($sp)    # save ra
	  addiu $fp, $sp, 8 # set up new fp
	  subu $sp, $sp, 12 # decrement sp to make space for locals/temps
	  lw $t0, 4($fp)	# load n
	  lw $t0, -4($fp)	# load n
	  li $t1, 1	# load 1
	  sub $t2, $t0, $t1
	  sw $t2, -12($fp)	# spill _tmp1
	  subu $sp, $sp, 4
	  lw $t0, -12($fp)	# load _tmp1
	  sw $t0, 4($sp)
	# LCall _factorial
	  jal _factorial	# jump to function
	  move $t2, $v0	# copy return value from $v0
	  add $sp, $sp, 4	# pop params off stack
	  sw $t2, -8($fp)	# store result into _tmp0
	  lw $t1, -8($fp)	# load _tmp0
	  mul $t2, $t0, $t1
	  sw $t2, -16($fp)	# spill _tmp2
	# Return _tmp2
	  lw $t2, -16($fp)	# load _tmp2
	  move $v0, $t2	    # assign return value into $v0
	  move $sp, $fp	    # pop callee frame off stack
	  lw $ra, -4($fp)	# restore saved ra
	  lw $fp, 0($fp)	# restore saved fp
	  jr $ra	    # return from function
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
	  subu $sp, $sp, 4  # decrement sp to make space for locals/temps
    # EndFunc
    # (below handles reaching end of fn body with no explicit return)
	  move $sp, $fp     # pop callee frame off stack
	  lw $ra, -4($fp)   # restore saved ra
	  lw $fp, 0($fp)    # restore saved fp
	  jr $ra        # return from function
