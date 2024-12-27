
killall arecord

while true; do
    # echo "working"
    sleep 1
    # 只接受 host 模式下工作
    usb_mode=$(cat /sys/devices/platform/soc/b2000000.usb/b2000000.dwc3/role)
    if [ "$usb_mode" == "host" ]; then
        echo "usb mode is host"

        # 复位确认声卡存在
        while true; do
            # 复位声卡
            sleep 0.1
            echo "0" > /sys/class/gpio/gpio117/value
            # sleep 0.5 这种复位不正确
            echo "1" > /sys/class/gpio/gpio117/value
            sleep 0.1

            # cat /proc/asound/cards
            card=$(cat /proc/asound/cards | grep M590Q)
            # echo $card
            if [ -z "$card" ]; then
                echo "no M590Q"
            else
                echo "have M590Q"
                break
            fi
        done

        # 产生配置，只运行一次，直到测试成功。

        audio_work=false

        if [ ! -f alsabat.cfg ]; then
            echo "alsabat.cfg not exist"
            
            amixer get "Headphone"
            amixer set "Headphone" 80%

            amixer get "Mic"
            amixer set "Mic" 100%

            alsabat -D default -P plughw:0,0 -C plughw:0,0 -f S16_LE -c 2 -r 44100 -n 0.1s > alsabat.cfg

            # 分析报告
            # alsabat.cfg 记录测试结果，并提供判断结果，在最后一行。
            # [working] [mic bug] [speaker] [unknown]
            
            # Channel 1 - Checking for target frequency 997.00 Hz
            # Amplitude: 243.7; Percentage: [0]
            # WARNING: Signal too weak!
            # Detected peak at 32.30 Hz of 13.30 dB
            # Total 13.3 dB from 32.30 to 32.30 Hz
            # FAIL: Peak freq too low 32.30 Hz
            # Detected peak at 1001.29 Hz of 22.05 dB
            # Total 26.9 dB from 958.23 to 1044.36 Hz
            # PASS: Peak detected at target frequency
            # Detected at least 2 signal(s) in total

        fi

        if grep -q "PASS: Peak detected at target frequency" alsabat.cfg; then
            audio_work=true
        else
            error_sum=$(grep -c "FAIL: Peak freq too low" alsabat.cfg)
            if [ $error_sum -gt 3 ]; then
                echo "no-speaker or mic too small"
            elif [ $error_sum -lt 2 ]; then
                echo "no-mic or mic broken"
            fi
        fi

        if [ "$audio_work" = false ]; then
            # 检测失败，则持续运行声音供测试分析。
            # 通过情况 PASS: Peak detected at target frequency
            # 不通过情况 FAIL: Peak freq too low
            # 超过 3 个以上  超过 3 个以上认为喇叭有问题，没出声，但咪头只是可能有问题，或声音小
            # 在 2 个以下认为咪头没接或损坏，没声音，更严重
            # 都属于有问题
            alsabat -D default -P plughw:0,0 -C plughw:0,0 -f S16_LE -c 2 -r 44100 -n 0.1s > alsabat.cfg
        else
            while true; do
                # 检查声卡是否存在
                card=$(cat /proc/asound/cards | grep M590Q)
                if [ -z "$card" ]; then
                    echo "run no M590Q"
                    # 如果检测到声卡掉了，停止 wmix 服务，并期望 声卡驱动 能够重新就绪。
                    # pgrep wmix | xargs kill -15
                    # 在 X3 上物理上这样断开，会引起 hungtask 异常，内核清理成 T 也不能完全消除对系统的影响。
                    # 此时系统无法正常 reboot ，建议遇到这种场合直接产生内核死循环触发看门狗重启
                    echo "deadloop 1100 0000"> /sys/kernel/debug/wdt_test
                    break
                fi

                if pidof wmix > /dev/null 2>&1; then
                    echo "wmix is running"
                else
                    echo "wmix is not running"
                    export LD_LIBRARY_PATH=./libs/lib && ./wmix -v 8 -vr 10 &
                fi

                sleep 1
            done
        fi

    fi
done

# make && export LD_LIBRARY_PATH=./libs/lib && ./wmix -v 8 -vr 10 -d

# echo "0" > /sys/class/gpio/gpio117/value

# echo "1" > /sys/class/gpio/gpio117/value