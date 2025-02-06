import wave
import socket
import struct
import audioop
from pydub import AudioSegment
import queue
import threading
import time

# 全局变量
audio_file = "./audio/1x16000.wav"
ip = "192.168.8.118"
port = 9832

# RTP头格式
rtp_header_format = "!BBHII"

# RTP头字段
version = 2
padding = 0
extension = 0
cc = 0
marker = 0
payload_type = 8  # G.711 A-law
ssrc = 123456789  # 随机选择一个SSRC

# 队列用于存储RTP包
rtp_queue = queue.Queue()

# 生产者线程：生成RTP包并放入队列
def producer():
    # 打开音频文件
    audio = AudioSegment.from_wav(audio_file)
    pcm_data = audio.raw_data
    alaw_data = audioop.lin2alaw(pcm_data, 2)

    # 初始化RTP头字段
    sequence_number = 0
    timestamp = 0

    # 分帧处理并填入队列
    frame_size = 160  # 每帧160字节（20ms）
    for i in range(0, len(alaw_data), frame_size):
        frame = alaw_data[i:i + frame_size]
        
        # 构造RTP头
        rtp_header = struct.pack(
            rtp_header_format,
            (version << 6) | (padding << 5) | (extension << 4) | cc,
            (marker << 7) | payload_type,
            sequence_number,
            timestamp,
            ssrc
        )
        
        # 构造RTP包
        rtp_packet = rtp_header + frame
        
        # 将RTP包填入队列
        rtp_queue.put(rtp_packet)
        
        # 更新序列号和时间戳
        sequence_number += 1
        timestamp += frame_size

    # 生产完成，标记队列结束
    rtp_queue.put(None)

# 消费者线程：从队列中读取RTP包并发送
def consumer():
    # 创建UDP套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    while True:
        rtp_packet = rtp_queue.get()
        if rtp_packet is None:
            break  # 队列结束，退出循环
        
        # 发送RTP包
        sock.sendto(rtp_packet, (ip, port))
        time.sleep(0.01)  # 每帧间隔20ms
    
    # 关闭套接字
    sock.close()

# 创建并启动线程
producer_thread = threading.Thread(target=producer)
consumer_thread = threading.Thread(target=consumer)

producer_thread.start()
consumer_thread.start()

# 等待线程结束
producer_thread.join()
consumer_thread.join()