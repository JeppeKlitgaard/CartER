/*
DebugUtils.h - Simple debugging utilities.
*/

#ifndef DEBUGUTILS_H
#define DEBUGUTILS_H

#include <Init.h>

#ifdef DEBUG
  #define DP(...) S.print(__VA_ARGS__)
  #define DPL(...) S.println(__VA_ARGS__)
#else
  #define DP(...)
  #define DPL(...)
#endif

#endif