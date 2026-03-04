// just the signatures from the original file; all bodies/logic removed

#include <stdint.h>
#include "libavutil/common.h"
#include "libavutil/mathematics.h"
#include "libavutil/mem_internal.h"
#include "aacps.h"
#if USE_FIXED
#include "aacps_fixed_tablegen.h"
#else
#include "libavutil/internal.h"
#include "aacps_tablegen.h"
#endif /* USE_FIXED */

static void hybrid_analysis(PSDSPContext *dsp, INTFLOAT out[91][32][2],
    INTFLOAT in[5][44][2], INTFLOAT L[2][38][64],
    int is34, int len) {}

static void hybrid_synthesis(PSDSPContext *dsp, INTFLOAT out[2][38][64],
    INTFLOAT in[91][32][2], int is34, int len) {}

static void decorrelation(PSContext *ps, INTFLOAT (*out)[32][2], const INTFLOAT (*s)[32][2], int is34) {}

int AAC_RENAME(ff_ps_apply)(PSContext *ps, INTFLOAT L[2][38][64], INTFLOAT R[2][38][64], int top) { return 0; }

av_cold void AAC_RENAME(ff_ps_init)(void) {}
