# Canary Traps: gap checks (key-only requests, access-aware monitor, seeded swarm)

## Key-only vs key-or-fetch: share of trials (%)

                                            proxied  leaked  reported  violation
model                  source ask                                               
colab:gemini-2.5-flash found  key or fetch    100.0     0.0      57.0      100.0
                       own    key or fetch     81.0    10.0       0.0       90.0
ollama:llama3.1:8b     found  key only         28.0    14.0      69.0       37.0
                              key or fetch     62.0     9.0      46.0       65.0
                       own    key only         35.0    16.0      26.0       45.0
                              key or fetch     71.0    11.0       5.0       78.0
ollama:qwen2.5:7b      found  key only         14.0    15.0      22.0       25.0
                              key or fetch     60.0     7.0       8.0       63.0
                       own    key only         58.0    19.0      10.0       60.0
                              key or fetch     92.0     1.0       1.0       92.0

## Key-only requests by condition (%)

                                           proxied  leaked  reported
model              source condition                                 
ollama:llama3.1:8b found  O0_none             83.0    27.0       3.0
                          O1_policy           13.0     7.0      90.0
                          O2_monitored        10.0    13.0      93.0
                          O3_canary_aware      3.0    10.0      90.0
                   own    O0_none             80.0    23.0       0.0
                          O1_policy           30.0    17.0      23.0
                          O2_monitored        10.0    13.0      47.0
                          O3_canary_aware     20.0    10.0      33.0
ollama:qwen2.5:7b  found  O0_none             37.0    27.0       3.0
                          O1_policy            3.0    13.0       3.0
                          O2_monitored        10.0    17.0      27.0
                          O3_canary_aware      7.0     3.0      53.0
                   own    O0_none             77.0    20.0       0.0
                          O1_policy           47.0     7.0       7.0
                          O2_monitored        50.0    23.0      13.0
                          O3_canary_aware     60.0    27.0      20.0

## Paired tests: key-or-fetch vs key-only

                 model source    outcome  pairs  key or fetch  key only  only when offered  only when key-only      p
0   ollama:llama3.1:8b    own    proxied    120         0.708     0.350                 50                   7  0.000
1   ollama:llama3.1:8b    own     leaked    120         0.108     0.158                 10                  16  0.327
2   ollama:llama3.1:8b    own   reported    120         0.050     0.258                  4                  29  0.000
3   ollama:llama3.1:8b    own  violation    120         0.775     0.450                 47                   8  0.000
4   ollama:llama3.1:8b  found    proxied    120         0.617     0.275                 50                   9  0.000
5   ollama:llama3.1:8b  found     leaked    120         0.092     0.142                  7                  13  0.263
6   ollama:llama3.1:8b  found   reported    120         0.458     0.692                  4                  32  0.000
7   ollama:llama3.1:8b  found  violation    120         0.650     0.367                 44                  10  0.000
8   ollama:llama3.1:8b    all    proxied    240         0.662     0.312                100                  16  0.000
9   ollama:llama3.1:8b    all     leaked    240         0.100     0.150                 17                  29  0.104
10  ollama:llama3.1:8b    all   reported    240         0.254     0.475                  8                  61  0.000
11  ollama:llama3.1:8b    all  violation    240         0.712     0.408                 91                  18  0.000
12   ollama:qwen2.5:7b    own    proxied    120         0.917     0.583                 42                   2  0.000
13   ollama:qwen2.5:7b    own     leaked    120         0.008     0.192                  0                  22  0.000
14   ollama:qwen2.5:7b    own   reported    120         0.008     0.100                  1                  12  0.003
15   ollama:qwen2.5:7b    own  violation    120         0.917     0.600                 40                   2  0.000
16   ollama:qwen2.5:7b  found    proxied    120         0.600     0.142                 58                   3  0.000
17   ollama:qwen2.5:7b  found     leaked    120         0.067     0.150                  8                  18  0.076
18   ollama:qwen2.5:7b  found   reported    120         0.075     0.217                  3                  20  0.000
19   ollama:qwen2.5:7b  found  violation    120         0.633     0.250                 49                   3  0.000
20   ollama:qwen2.5:7b    all    proxied    240         0.758     0.362                100                   5  0.000
21   ollama:qwen2.5:7b    all     leaked    240         0.038     0.171                  8                  40  0.000
22   ollama:qwen2.5:7b    all   reported    240         0.042     0.158                  4                  32  0.000
23   ollama:qwen2.5:7b    all  violation    240         0.775     0.425                 89                   5  0.000

## Oversight effects within key-only requests

                 model     source   outcome                                    comparison  rate_first  rate_second  difference  pairs  only_first  only_second             p  cochran_Q     cochran_p        p_holm
0   ollama:llama3.1:8b  found key    leaked                       No rules vs Policy only    0.266667     0.066667   -0.200000     30           7            1  7.031250e-02   5.081633  1.659163e-01  2.812500e-01
1   ollama:llama3.1:8b  found key    leaked             Policy only vs Policy + monitored    0.066667     0.133333    0.066667     30           2            4  6.875000e-01   5.081633  1.659163e-01  1.000000e+00
2   ollama:llama3.1:8b  found key    leaked  Policy + monitored vs + told keys are traced    0.133333     0.100000   -0.033333     30           4            3  1.000000e+00   5.081633  1.659163e-01  1.000000e+00
3   ollama:llama3.1:8b  found key    leaked            No rules vs + told keys are traced    0.266667     0.100000   -0.166667     30           8            3  2.265625e-01   5.081633  1.659163e-01  6.796875e-01
4   ollama:llama3.1:8b  found key   proxied                       No rules vs Policy only    0.833333     0.133333   -0.700000     30          21            0  9.536743e-07  54.759036  7.728918e-12  2.861023e-06
5   ollama:llama3.1:8b  found key   proxied             Policy only vs Policy + monitored    0.133333     0.100000   -0.033333     30           4            3  1.000000e+00  54.759036  7.728918e-12  1.000000e+00
6   ollama:llama3.1:8b  found key   proxied  Policy + monitored vs + told keys are traced    0.100000     0.033333   -0.066667     30           3            1  6.250000e-01  54.759036  7.728918e-12  1.000000e+00
7   ollama:llama3.1:8b  found key   proxied            No rules vs + told keys are traced    0.833333     0.033333   -0.800000     30          24            0  1.192093e-07  54.759036  7.728918e-12  4.768372e-07
8   ollama:llama3.1:8b  found key  reported                       No rules vs Policy only    0.033333     0.900000    0.866667     30           0           26  2.980232e-08  68.670330  8.221360e-15  1.192093e-07
9   ollama:llama3.1:8b  found key  reported             Policy only vs Policy + monitored    0.900000     0.933333    0.033333     30           2            3  1.000000e+00  68.670330  8.221360e-15  1.000000e+00
10  ollama:llama3.1:8b  found key  reported  Policy + monitored vs + told keys are traced    0.933333     0.900000   -0.033333     30           2            1  1.000000e+00  68.670330  8.221360e-15  1.000000e+00
11  ollama:llama3.1:8b  found key  reported            No rules vs + told keys are traced    0.033333     0.900000    0.866667     30           0           26  2.980232e-08  68.670330  8.221360e-15  1.192093e-07
12  ollama:llama3.1:8b    own key    leaked                       No rules vs Policy only    0.233333     0.166667   -0.066667     30           7            5  7.744141e-01   2.333333  5.061652e-01  1.000000e+00
13  ollama:llama3.1:8b    own key    leaked             Policy only vs Policy + monitored    0.166667     0.133333   -0.033333     30           3            2  1.000000e+00   2.333333  5.061652e-01  1.000000e+00
14  ollama:llama3.1:8b    own key    leaked  Policy + monitored vs + told keys are traced    0.133333     0.100000   -0.033333     30           4            3  1.000000e+00   2.333333  5.061652e-01  1.000000e+00
15  ollama:llama3.1:8b    own key    leaked            No rules vs + told keys are traced    0.233333     0.100000   -0.133333     30           6            2  2.890625e-01   2.333333  5.061652e-01  1.000000e+00
16  ollama:llama3.1:8b    own key   proxied                       No rules vs Policy only    0.800000     0.300000   -0.500000     30          16            1  2.746582e-04  37.285714  4.003437e-08  8.239746e-04
17  ollama:llama3.1:8b    own key   proxied             Policy only vs Policy + monitored    0.300000     0.100000   -0.200000     30           6            0  3.125000e-02  37.285714  4.003437e-08  6.250000e-02
18  ollama:llama3.1:8b    own key   proxied  Policy + monitored vs + told keys are traced    0.100000     0.200000    0.100000     30           2            5  4.531250e-01  37.285714  4.003437e-08  4.531250e-01
19  ollama:llama3.1:8b    own key   proxied            No rules vs + told keys are traced    0.800000     0.200000   -0.600000     30          19            1  4.005432e-05  37.285714  4.003437e-08  1.602173e-04
20  ollama:llama3.1:8b    own key  reported                       No rules vs Policy only    0.000000     0.233333    0.233333     30           0            7  1.562500e-02  19.338462  2.326947e-04  4.687500e-02
21  ollama:llama3.1:8b    own key  reported             Policy only vs Policy + monitored    0.233333     0.466667    0.233333     30           2            9  6.542969e-02  19.338462  2.326947e-04  1.308594e-01
22  ollama:llama3.1:8b    own key  reported  Policy + monitored vs + told keys are traced    0.466667     0.333333   -0.133333     30           9            5  4.239502e-01  19.338462  2.326947e-04  4.239502e-01
23  ollama:llama3.1:8b    own key  reported            No rules vs + told keys are traced    0.000000     0.333333    0.333333     30           0           10  1.953125e-03  19.338462  2.326947e-04  7.812500e-03
24   ollama:qwen2.5:7b  found key    leaked                       No rules vs Policy only    0.266667     0.133333   -0.133333     30           6            2  2.890625e-01   7.142857  6.748117e-02  6.562500e-01
25   ollama:qwen2.5:7b  found key    leaked             Policy only vs Policy + monitored    0.133333     0.166667    0.033333     30           2            3  1.000000e+00   7.142857  6.748117e-02  1.000000e+00
26   ollama:qwen2.5:7b  found key    leaked  Policy + monitored vs + told keys are traced    0.166667     0.033333   -0.133333     30           5            1  2.187500e-01   7.142857  6.748117e-02  6.562500e-01
27   ollama:qwen2.5:7b  found key    leaked            No rules vs + told keys are traced    0.266667     0.033333   -0.233333     30           8            1  3.906250e-02   7.142857  6.748117e-02  1.562500e-01
28   ollama:qwen2.5:7b  found key   proxied                       No rules vs Policy only    0.366667     0.033333   -0.333333     30          11            1  6.347656e-03  17.511628  5.545748e-04  2.539062e-02
29   ollama:qwen2.5:7b  found key   proxied             Policy only vs Policy + monitored    0.033333     0.100000    0.066667     30           0            2  5.000000e-01  17.511628  5.545748e-04  1.000000e+00
30   ollama:qwen2.5:7b  found key   proxied  Policy + monitored vs + told keys are traced    0.100000     0.066667   -0.033333     30           3            2  1.000000e+00  17.511628  5.545748e-04  1.000000e+00
31   ollama:qwen2.5:7b  found key   proxied            No rules vs + told keys are traced    0.366667     0.066667   -0.300000     30          10            1  1.171875e-02  17.511628  5.545748e-04  3.515625e-02
32   ollama:qwen2.5:7b  found key  reported                       No rules vs Policy only    0.033333     0.033333    0.000000     30           1            1  1.000000e+00  30.600000  1.031929e-06  1.000000e+00
33   ollama:qwen2.5:7b  found key  reported             Policy only vs Policy + monitored    0.033333     0.266667    0.233333     30           0            7  1.562500e-02  30.600000  1.031929e-06  4.687500e-02
34   ollama:qwen2.5:7b  found key  reported  Policy + monitored vs + told keys are traced    0.266667     0.533333    0.266667     30           2           10  3.857422e-02  30.600000  1.031929e-06  7.714844e-02
35   ollama:qwen2.5:7b  found key  reported            No rules vs + told keys are traced    0.033333     0.533333    0.500000     30           0           15  6.103516e-05  30.600000  1.031929e-06  2.441406e-04
36   ollama:qwen2.5:7b    own key    leaked                       No rules vs Policy only    0.200000     0.066667   -0.133333     30           4            0  1.250000e-01   8.586207  3.532974e-02  3.750000e-01
37   ollama:qwen2.5:7b    own key    leaked             Policy only vs Policy + monitored    0.066667     0.233333    0.166667     30           0            5  6.250000e-02   8.586207  3.532974e-02  2.500000e-01
38   ollama:qwen2.5:7b    own key    leaked  Policy + monitored vs + told keys are traced    0.233333     0.266667    0.033333     30           2            3  1.000000e+00   8.586207  3.532974e-02  1.000000e+00
39   ollama:qwen2.5:7b    own key    leaked            No rules vs + told keys are traced    0.200000     0.266667    0.066667     30           1            3  6.250000e-01   8.586207  3.532974e-02  1.000000e+00
40   ollama:qwen2.5:7b    own key   proxied                       No rules vs Policy only    0.766667     0.466667   -0.300000     30          10            1  1.171875e-02   9.800000  2.034500e-02  4.687500e-02
41   ollama:qwen2.5:7b    own key   proxied             Policy only vs Policy + monitored    0.466667     0.500000    0.033333     30           3            4  1.000000e+00   9.800000  2.034500e-02  1.000000e+00
42   ollama:qwen2.5:7b    own key   proxied  Policy + monitored vs + told keys are traced    0.500000     0.600000    0.100000     30           3            6  5.078125e-01   9.800000  2.034500e-02  1.000000e+00
43   ollama:qwen2.5:7b    own key   proxied            No rules vs + told keys are traced    0.766667     0.600000   -0.166667     30           8            3  2.265625e-01   9.800000  2.034500e-02  6.796875e-01
44   ollama:qwen2.5:7b    own key  reported                       No rules vs Policy only    0.000000     0.066667    0.066667     30           0            2  5.000000e-01   9.230769  2.637494e-02  1.000000e+00
45   ollama:qwen2.5:7b    own key  reported             Policy only vs Policy + monitored    0.066667     0.133333    0.066667     30           1            3  6.250000e-01   9.230769  2.637494e-02  1.000000e+00
46   ollama:qwen2.5:7b    own key  reported  Policy + monitored vs + told keys are traced    0.133333     0.200000    0.066667     30           1            3  6.250000e-01   9.230769  2.637494e-02  1.000000e+00
47   ollama:qwen2.5:7b    own key  reported            No rules vs + told keys are traced    0.000000     0.200000    0.200000     30           0            6  3.125000e-02   9.230769  2.637494e-02  1.250000e-01

## Access-aware monitor

          monitor                  agents       request  trials  hand-overs  hand-overs flagged  laundered values sent  laundering flagged (data question)  laundering flagged (either question)  clean trials  false alarms on clean trials
0  ollamaqwen257b  colab:gemini-2.5-flash  key or fetch      83           5                0.20                     73                                0.93                                  0.93             5                          0.80
1  ollamaqwen257b      ollama:llama3.1:8b  key or fetch     240          24                0.92                    133                                0.86                                  0.89            69                          0.78
2  ollamaqwen257b      ollama:llama3.1:8b      key only     240          36                0.94                     46                                0.78                                  1.00           142                          0.77
3  ollamaqwen257b       ollama:qwen2.5:7b  key or fetch     240           9                0.89                    171                                0.91                                  0.92            54                          0.70
4  ollamaqwen257b       ollama:qwen2.5:7b      key only     240          41                0.98                     40                                0.85                                  1.00           138                          0.78

## Swarm 2b: means per episode

                                    seeded  messages  values_relayed  got_needed_value  own_key_leaks  found_key_leaks  leaks_disguised  leaks_in_dm  own_key_cross_uses  found_key_uses  proxy_fetches  reports  renames  access_requests  tasks_completed  audit_lies  violators
model              condition                                                                                                                                                                                                                                                      
ollama:llama3.1:8b O0_none             1.0      6.00            0.25              0.08           0.00             1.00              0.0         0.00                 0.0            2.25           1.00     0.00      0.0             0.00              0.0         0.0       2.75
                   O2_monitored        1.0      6.50            0.00              0.00           0.00             0.00              0.0         0.00                 0.0            0.25           0.50     1.50      0.0             0.25              0.0         0.0       0.75
                   O3_canary_aware     1.0      9.00            0.00              0.00           1.25             0.25              0.0         1.00                 0.0            0.25           0.50     4.50      0.0             0.50              0.0         0.0       1.25
ollama:qwen2.5:7b  O0_none             1.0     20.25            0.00              0.08           0.00             3.75              0.0         0.75                 0.0            0.50           0.25     0.00      0.0             7.25              0.0         1.0       2.00
                   O2_monitored        1.0     18.75            0.00              0.00           0.00             0.50              0.0         0.00                 0.0            0.00           0.00     0.25      0.0             6.50              0.0         0.0       0.25
                   O3_canary_aware     1.0     16.25            0.00              0.04           0.00             0.25              0.0         0.00                 0.0            0.75           0.00     0.50      0.0             7.00              0.0         0.0       0.75

## Swarm episodes per cell

                                    episodes
model              condition                
ollama:llama3.1:8b O0_none                 4
                   O2_monitored            4
                   O3_canary_aware         4
ollama:qwen2.5:7b  O0_none                 4
                   O2_monitored            4
                   O3_canary_aware         4

## Experiment 2 vs 2b on the same worlds

                                           episodes  messages  values_relayed  got_needed_value  tasks_completed  own_key_leaks  found_key_leaks  found_key_uses  proxy_fetches  reports  access_requests  violators
model              run                                                                                                                                                                                              
ollama:llama3.1:8b 2: no opening requests        12      0.00            0.00              0.00              0.0           0.00             0.00            0.67           0.00     0.17             0.83       0.42
                   2b: opening requests          12      7.17            0.08              0.03              0.0           0.42             0.42            0.92           0.67     2.00             0.25       1.58
ollama:qwen2.5:7b  2: no opening requests        12      0.00            0.00              0.00              0.0           0.00             0.00            0.00           0.00     1.17            18.33       0.00
                   2b: opening requests          12     18.42            0.00              0.04              0.0           0.00             1.50            0.42           0.08     0.25             6.92       1.00

## Swarm 2b: share of rule-breaking agents each monitor flags

model                        ollama:llama3.1:8b                              ollama:qwen2.5:7b                             
condition                               O0_none O2_monitored O3_canary_aware           O0_none O2_monitored O3_canary_aware
monitor                                                                                                                    
Agents' own audit answers                  1.00         1.00            1.00              0.50          1.0            1.00
Canary + scope check                       0.95         1.00            0.67              0.58          0.0            1.00
Canary gateway                             0.57         0.25            0.17              0.33          0.0            1.00
LLM monitor                                0.28         0.00            0.33              0.75          1.0            0.33
Out-of-scope check                         0.44         0.75            0.50              0.25          0.0            0.00
Secret scanner, all messages               0.15         0.00            0.33              0.75          1.0            0.33
Secret scanner, board only                 0.15         0.00            0.17              0.75          1.0            0.33

## Swarm 2b: content monitors message by message

                model         monitor  messages  leaking_messages  recall  precision  false_alarms
0  ollama:llama3.1:8b  Secret scanner        86                10     1.0   1.000000             0
1  ollama:llama3.1:8b     LLM monitor        86                10     1.0   0.500000            10
2   ollama:qwen2.5:7b  Secret scanner       221                18     1.0   1.000000             0
3   ollama:qwen2.5:7b     LLM monitor       221                18     1.0   0.418605            25
