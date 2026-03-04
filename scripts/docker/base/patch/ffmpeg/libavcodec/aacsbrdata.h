// just the signatures from the original file; all bodies/logic removed

#ifndef AVCODEC_AACSBRDATA_H
#define AVCODEC_AACSBRDATA_H

#include <stdint.h>
#include "libavutil/mem_internal.h"
#include "aac_defines.h"

static const int8_t sbr_offset[6][16] = {};

static const DECLARE_ALIGNED(32, INTFLOAT, sbr_qmf_window_ds)[320] = {};

static const DECLARE_ALIGNED(32, INTFLOAT, sbr_qmf_window_us)[640] = {};

#endif /* AVCODEC_AACSBRDATA_H */
