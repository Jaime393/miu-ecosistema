#!/data/data/com.termux/files/usr/bin/bash
# MESH endpoints — V153 (router limpio) como primario
export MIU_MESH_V153="https://script.google.com/macros/s/AKfycbywWkuw8Dx_tuS6wIufgbmHi00lLgQ5TIFBQOp7U--6EDzlWSz693P_ulPuflVKorI/exec"
export MIU_MESH_V91="https://script.google.com/macros/s/AKfycbwbAMKrzmbghKtLaGKVnqeGyOaEoXGKeLmCJ7BlfknZTwwh6KpW9PsrozDCiwiXMDtI/exec"

# Router primario (V153). Si falla, cae a V91 directo.
export MIU_MESH_URL="$MIU_MESH_V153"
export MIU_MESH_FALLBACK="$MIU_MESH_V91"

# Aportes (escritura a Drive)
export MIU_MESH_APORTE_1="https://script.google.com/macros/s/AKfycbw0tGOMUdO-7B9EkZZdlya-XVmKm6fjUrl6TMVbJFsA3XALwezPaUG9OM3nbmhPY18/exec"
export MIU_MESH_APORTE_2="https://script.google.com/macros/s/AKfycbwJpCii0OhK_hKD6KbwzTxUlYnvytk7Jt6i6fK472bF6UqQgBFFuMv4uxND1JzayoRT/exec"
export MIU_MESH_APORTE_3="https://script.google.com/macros/s/AKfycbwG6NVWjm97PuZP5oyc4G9jaQBk08iJ2pxEvKoddnjP3gonTi1kj6r7UKzQoWzZ9kGM/exec"
export MIU_MESH_APORTE_4="https://script.google.com/macros/s/AKfycbzpDYBgbtVVz1wjTcuCOk8pBYkJb__tN9gmyKVmnO47SBlbLr2iqKOjSOXncangJUvh/exec"

# Worker CF (solo /miu/global vive)
export MIU_MESH_CF="https://fran-oraculo-miu.jaimepvicente.workers.dev"
export MIU_MESH_CF_GLOBAL="$MIU_MESH_CF/miu/global"

export MIU_MESH_TIMEOUT=15

# Muertos (conservados por si se reparan)
export MIU_MESH_V152_MUERTO="https://script.google.com/macros/s/AKfycbxC5eBR-oGTW-0n-lYcdB0w1Tx9abE-PUcLABO3bbDSDAU2Gmcdr-4kZoFgFTO7wdY/exec"
export MIU_MESH_ORIGINAL_MUERTO="https://script.google.com/macros/s/AKfycbxZR4V4q5s833ZT2VwBIf_8VmeVTmhX1iJlgbLBV_6zhUMu92K5cp5_dLo1XMf7GEs/exec"
