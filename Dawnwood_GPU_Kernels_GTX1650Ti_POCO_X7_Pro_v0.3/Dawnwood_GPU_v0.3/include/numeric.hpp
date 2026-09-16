#pragma once
#include "numeric_types.inc"
#define DW_OP_ARGUMENT , ops
#include "numeric_evolve.inc"
static_assert(sizeof(State)==128,"State ABI");
static_assert(sizeof(Operator)==64,"Operator ABI");
static_assert(sizeof(Config)==64,"Push ABI");
