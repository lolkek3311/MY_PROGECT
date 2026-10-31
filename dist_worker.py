#!/usr/bin/env python3
"""
Distributed ECM Worker for ISO challenge.
Runs GMP-ECM on all available CPU cores.
"""

import subprocess
import concurrent.futures
import time
import os
import sys
import multiprocessing
import random

# 616-digit cofactor containing the 128-bit prime p
COFACTOR = "1457506062875932817869177975145756628778829486130694151675619410000045233025452318197087491186659039504564609855820125742244854384953937587718871938163914748886160827115674300836373948031539315693609126200833021512260426564405247620393241717756612569519174506217307654295046339196604177967426998112643020893194149880926399070708798100193542243954578877626636216188267061594182902222212311125262838762245222060004758747396821275609416435361794797593067428291811253805770902740232478897198198644156741483763383085132396412471374750529542481663134137726652394951656939253795325420794562139234602187068800874902822025171"

def run_curve(curve_id, b1):
    # Pass a random sigma seed to ensure totally distinct curves across parallel runners
    sigma = random.randint(1000, 2**32 - 1)
    cmd = ['ecm', '-q', '-sigma', str(sigma), str(b1)]
    p = subprocess.run(cmd, input=COFACTOR, capture_output=True, text=True)
    out = p.stdout.strip()
    if out:
        for line in out.splitlines():
            line = line.strip()
            if line.isdigit() and len(line) > 1 and line != COFACTOR:
                return line
    return None

def main():
    workers = multiprocessing.cpu_count()
    b1 = 3000000
    print(f"[+] Starting ECM on {workers} CPU cores with B1={b1}...", flush=True)
    print(f"[+] Target cofactor length: {len(COFACTOR)} digits", flush=True)
    
    t0 = time.time()
    curves_done = 0
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(run_curve, i, b1): i for i in range(workers * 2)}
        curve_counter = workers * 2
        
        while futures:
            done, _ = concurrent.futures.wait(futures, timeout=5, return_when=concurrent.futures.FIRST_COMPLETED)
            for f in done:
                curves_done += 1
                res = f.result()
                del futures[f]
                
                if res:
                    print(f"\n{'='*60}\n[!!!] FACTOR FOUND:\n{res}\n{'='*60}\n", flush=True)
                    with open("FOUND_FACTOR.txt", "w") as out_f:
                        out_f.write(res + "\n")
                    return
                
                rate = curves_done / (time.time() - t0) * 60
                print(f"[+] Curve {curves_done} completed ({rate:.1f} curves/min, elapsed: {int(time.time() - t0)}s)", flush=True)
                
                futures[executor.submit(run_curve, curve_counter, b1)] = curve_counter
                curve_counter += 1

if __name__ == '__main__':
    main()
