import os
from pathlib import Path
import asyncio

WMIX_MSG_PATH = "/tmp/wmix"
WMIX_MSG_ID = 119
WMIX_MSG_BUFF_SIZE = 128

WMT_VOLUME = 1           # 设置音量
WMT_PLAY_MUTEX = 2      # 互斥播放文件
WMT_PLAY_MIX = 3         # 混音播放文件
WMT_FIFO_PLAY = 4        # fifo播放wav流
WMT_RESET = 5            # 复位
WMT_FIFO_RECORD = 6      # fifo录音wav流
WMT_RECORD_WAV = 7       # 录音wav文件
WMT_CLEAN_LIST = 8       # 清空播放列表
WMT_PLAY_FIRST = 9       # 排头播放
WMT_PLAY_LAST = 10       # 排尾播放
WMT_RTP_SEND_PCMA = 11   # rtp send pcma
WMT_RTP_RECV_PCMA = 12   # rtp recv pcma
WMT_RECORD_AAC = 13      # 录音aac文件
WMT_MEM_SW = 14          # 开/关 shmem
WMT_WEBRTC_VAD_SW = 15   # 开/关 webrtc.vad 人声识别,录音辅助,没人说话时主动静音
WMT_WEBRTC_AEC_SW = 16   # 开/关 webrtc.aec 回声消除
WMT_WEBRTC_NS_SW = 17    # 开/关 webrtc.ns 噪音抑制(录音)
WMT_WEBRTC_NS_PA_SW = 18 # 开/关 webrtc.ns 噪音抑制(播音)
WMT_WEBRTC_AGC_SW = 19   # 开/关 webrtc.agc 自动增益
WMT_RW_TEST = 20         # 自收发测试
WMT_VOLUME_MIC = 21      # 设置录音音量
WMT_VOLUME_AGC = 22      # 设置录音音量增益

WMT_LOG_SW = 100 # 开关log
WMT_INFO = 101   # 打印信息

# 定义单例类 AudioExcutor
class AudioExcutor():
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AudioExcutor, cls).__new__(cls)
            cls.setup()  # 在创建实例时自动调用 setup 方法
        return cls._instance

    def __init__(self):
        super().__init__()
        self._id = 0
        self.MSG_INIT()

    def MSG_INIT(self):
        try:
            import sysv_ipc
            msg_key = sysv_ipc.ftok(WMIX_MSG_PATH, WMIX_MSG_ID, silence_warning=True)
            self.msg_queue = sysv_ipc.MessageQueue(msg_key, flags=sysv_ipc.IPC_CREAT, mode=0o666)
        except Exception as e:
            print(e)
            return -1
        except sysv_ipc.Error as e:
            print(f"wmix: msgget err: {e}")
            return -1

    def auto_path(self, id=0):
        if id <= 0:
            self._id += 1
            id = (os.getpid() % 1000000) * 1000 + self._id
        return f"{WMIX_MSG_PATH}/{id}"
    
    def set_value(self, vtype:int, value:int):
        tmp = bytes(value.to_bytes(1,'big'))+b'\x00'
        self.msg_queue.send(tmp, type=vtype, block=False)

    @staticmethod
    def set_volume(value:int):
        AudioExcutor().set_value(WMT_VOLUME,value)

    def play(self, wavOrMp3:str, backgroundReduce:int, repeatInterval:int, order:int)->int:
        if wavOrMp3[0] == ".":
            wavOrMp3 = os.getcwd() + "/" + wavOrMp3
        msg_path = self.auto_path()
        msgtype = (backgroundReduce * 0x100) + (repeatInterval * 0x10000) + order
        value = wavOrMp3.encode() + b"\x00" + msg_path.encode() + b"\x00"
        self.msg_queue.send(value, type=msgtype, block=False)
        return int(msg_path.split("/")[-1])
    
    def kill(self, id=0):
        if id == 0:
            self.msg_queue.send(b"\x00", type=WMT_CLEAN_LIST, block=False)
        else:
            msgpath = self.auto_path(id)
            try:
                import sysv_ipc
                msg_key = sysv_ipc.ftok(msgpath, WMIX_MSG_ID, silence_warning=True)
                msg_queue = sysv_ipc.MessageQueue(msg_key, flags=sysv_ipc.IPC_CREAT, mode=0o666)
                msg_queue.remove()
            except Exception as e:
                print(e)
                return -1
            except sysv_ipc.Error as e:
                print(f"wmix: msgget err: {e}")
                return -1

    # def rtp(self, ip:str, port:int, chn:int, freq:int, isSend:bool):
    #     msg_path = self.auto_path()
    #     value = bytearray(128)  # 初始化一个足够大的 bytearray

    #     value[0] = chn
    #     value[1] = 16
    #     value[2:4] = freq.to_bytes(2, byteorder='big')  # 频率（2 字节，大端）
    #     value[4:6] = port.to_bytes(2, byteorder='big')  # 端口号（2 字节，大端）

    #     ip_bytes = ip.encode()
    #     msgPath_bytes = msg_path.encode()

    #     ip_offset = 6
    #     msgPath_offset = ip_offset + len(ip_bytes) + 1

    #     value[ip_offset:ip_offset + len(ip_bytes)] = ip_bytes
    #     value[ip_offset + len(ip_bytes)] = 0  # 添加 '\0' 分隔符
    #     value[msgPath_offset:msgPath_offset + len(msgPath_bytes)] = msgPath_bytes

    #     self.msg_queue.send(value, type=WMT_RTP_SEND_PCMA if isSend else WMT_RTP_RECV_PCMA, block=False)
    #     return int(msg_path.split("/")[-1])

    def record_stream_open(self, channels, sample, freq):
        # self.MSG_INIT()
        msg_path = self.auto_path().encode()
        value = bytearray(128)
        value[0] = channels
        value[1] = sample
        value[2:4] = freq.to_bytes(2, byteorder='big')  # 频率（2 字节，大端）
        value[4:4+len(msg_path)] = msg_path

        # print(value)

        self.msg_queue.send(value, type=WMT_FIFO_RECORD, block=False)
        return msg_path

    def stream_open(self, channels, sample, freq, backgroundReduce):
        # self.MSG_INIT()
        msg_path = self.auto_path().encode()
        value = bytearray(128)
        value[0] = channels
        value[1] = sample
        value[2:4] = freq.to_bytes(2, byteorder='big')  # 频率（2 字节，大端）
        value[4:4+len(msg_path)] = msg_path

        # print(msg_path)

        self.msg_queue.send(value, type=WMT_FIFO_PLAY + backgroundReduce * 0x100, block=False)
        return msg_path

    @classmethod
    def setup(cls):
        current_dir = Path(__file__).parents[2]
        cls.base_path = os.path.join(current_dir, 'config', 'resources', 'audio')
        # print("Base path:", cls.base_path)


async def main():
    # nc = await nats.connect("nats://localhost:4222")
    dev = AudioExcutor()
    play_path = dev.stream_open(1,16,16000,3)
    read_path = dev.record_stream_open(1,16,16000)
    import time

    time.sleep(1)
    play_file = open(play_path, "wb")
    read_file = open(read_path, "rb")

    while True:
        play_file.write(read_file.read(1024))
    
    # sub = await nc.subscribe("services.audio.ctrl")
    # sch = Scheduler()
    # async def check(loop):
    #     while True:
    #         if len(sch) > 0:
    #             tmp = sch.heap[0].cmd
    #             js = json.loads(tmp)
    #             if js["type"] == "kill":
    #                 sch.pop()
    #                 AudioExcutor().kill()
    #             elif js["type"] == "volume":
    #                 sch.pop()
    #                 AudioExcutor().set_volume(js["val1"])
    #             elif js["type"] == "play":
    #                 if js["val4"] == WMT_PLAY_LAST and os.listdir(WMIX_MSG_PATH):
    #                     continue
    #                 sch.pop()
    #                 AudioExcutor().play(js["val1"], js["val2"], js["val3"], js["val4"])

    #         await asyncio.sleep(0.1)
    # loop = asyncio.get_running_loop()
    # loop.create_task(check(loop))
    # while True:
    #     msg = await sub.next_msg(None)
    #     try:
    #         json.loads(msg.data)
    #     except:
    #         continue
    #     sch.push("audio", msg.data, 5)
        # await nc.publish("services.screen.info", dev.cmd(msg.data).encode())

if __name__ == "__main__":
    asyncio.run(main())