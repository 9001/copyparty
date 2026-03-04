// just the signatures from the original file; all bodies/logic removed

#define USE_FIXED 1

#include "aac.h"
#include "sbr.h"
#include "aacsbr.h"
#include "aacsbrdata.h"
#include "aacps.h"
#include "sbrdsp.h"
#include "libavutil/internal.h"
#include "libavutil/libm.h"
#include "libavutil/avassert.h"

#include <stdint.h>
#include <float.h>
#include <math.h>

static void aacsbr_func_ptr_init(AACSBRContext *c);
static const int CONST_RECIP_LN2 = Q31(0.7);
static const int CONST_076923    = Q31(0.7);

static const int fixed_log_table[] = {Q31(0)};

static int fixed_log(int x) {return 1;}

static void make_bands(int16_t* bands, int start, int stop, int num_bands) {}

static void sbr_dequant(SpectralBandReplication *sbr, int id_aac) {}

static void sbr_hf_inverse_filter(SBRDSPContext *dsp,
    int (*alpha0)[2], int (*alpha1)[2],
    const int X_low[32][40][2], int k0) {}

static void sbr_chirp(SpectralBandReplication *sbr, SBRData *ch_data) {}

static void sbr_gain_calc(SpectralBandReplication *sbr,
    SBRData *ch_data, const int e_a[2]) {}

static void sbr_hf_assemble(int Y1[38][64][2],
    const int X_high[64][40][2],
    SpectralBandReplication *sbr, SBRData *ch_data,
    const int e_a[2]) {}

#include "aacsbr_template.c"
