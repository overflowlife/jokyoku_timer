#python 3.9
#coding: UTF-8(cp65001)
#developer: twitter@overflowlife
import cv2
import pyautogui
import time
import tkinter as tk
from threading import Thread
import winsound
import configparser


#History
#me: 127('20/10/12)
#me: 132('20/12/24)
#belu: 118 ('20/10/14)

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        ######### Setting
        self.username = ''
        self.timeOverture = 120
        self.searchDelay = 1.0
        self.UseImg = 'Canny'
        self.cannyMinVal = 600
        self.cannyMaxVal = 600
        try:
            inifile = configparser.ConfigParser()
            inifile.read('./jokyoku.ini','UTF-8' )
            self.username = inifile.get('general', 'username')
            self.timeOverture = int(inifile.get('general', 'jokyokutime'))
            self.searchDelay = float(inifile.get('general', 'searchinterval'))
            self.UseImg = inifile.get('filter', 'processor')

            self.cannyMinVal = int(inifile.get('filter', 'cannyMinVal'))
            self.cannyMaxVal = int(inifile.get('filter', 'cannyMaxVal'))
        except:
            print('config read error.')


        self.resetToken = False

        #フレームの設定
        self.master.title("序曲タイマー")
        self.master.attributes("-topmost", True)

        self.pack()
        self.createWidget()
    
        #検索先画像1のインポート、グレースケール、2値化
        musicImg = cv2.imread('music_raw.png')
        musicImgGray = cv2.cvtColor(musicImg, cv2.COLOR_BGR2GRAY)
        cv2.imwrite('tmp_musicImgGray.png', musicImgGray)
        binret, self.musicImgBinary = cv2.threshold(musicImgGray, 247, 255, cv2.THRESH_BINARY)
        self.musicImgCanny = cv2.Canny(self.musicImgBinary, self.cannyMinVal, self.cannyMaxVal)
        cv2.imwrite('tmp_musicImgBinary.png', self.musicImgBinary)
        cv2.imwrite('tmp_musicImgCanny.png', self.musicImgCanny)
        self.musicH, self.musicW = musicImg.shape[:-1]

        #検索先画像2のインポート、グレースケール、2値化
        playerImg = cv2.imread('player_raw.png')
        playerImgGray = cv2.cvtColor(playerImg, cv2.COLOR_BGR2GRAY)
        cv2.imwrite('tmp_playerImgGray.png', playerImgGray)
        binret, self.playerImgBinary = cv2.threshold(playerImgGray, 247, 255, cv2.THRESH_BINARY)
        self.playerImgCanny = cv2.Canny(self.playerImgBinary, self.cannyMinVal, self.cannyMaxVal)
        cv2.imwrite('tmp_playerImgBinary.png', self.playerImgBinary)
        cv2.imwrite('tmp_playerImgCanny.png', self.playerImgCanny)
        self.playerH, self.playerW = playerImg.shape[:-1]

        self.Run()

    def btClicked(self):
        self.resetToken = True

    def Run(self):
            self.labelText.set('I am watching.')
            self.Proc = Thread(target = self.Watch)
            self.Proc.start()

    def Watch(self):
        self.isCountDown = False
        cnt = 1
        while True:
            cnt = cnt+1
            print('I am watching' + str(cnt))
            if(self.SearchForMusic() and not self.isCountDown):
                self.startTime = time.time()
                freq = 220 # Set frequency To 2500 Hertz
                dur = 200 # Set duration To 1000 ms == 1 second
                winsound.Beep(freq, dur)
                if(self.tuanBool.get()):
                    print('Tuan mode countdown start!')
                    p = Thread(target=self.countDownTuan)
                    p.start()
                else:
                    print('Normal mode countdown start!')
                    p = Thread(target=self.countDown)
                    p.start()
            time.sleep(self.searchDelay)
        
    def SearchForMusic(self):
        #キャプチャ取得、クリッピング、2値化
        capture = pyautogui.screenshot()
        capture.save('tmp_capture.png')
        capture = cv2.imread('tmp_capture.png')
        capH, capW = capture.shape[:-1]
        captureClipped = capture[int(capH*0.1): int(capH*0.9), int(capW*0.1): int(capW*0.9)]
        captureClippedGray = cv2.cvtColor(captureClipped, cv2.COLOR_BGR2GRAY)
        cv2.imwrite('tmp_captureClippedGray.png', captureClippedGray)
        binret, captureClippedBinary = cv2.threshold(captureClippedGray, 247, 255, cv2.THRESH_BINARY)
        captureClippedCanny = cv2.Canny(captureClippedBinary, self.cannyMinVal, self.cannyMaxVal)
        cv2.imwrite('tmp_captureClippedCanny.png', captureClippedCanny)
        cv2.imwrite('tmp_captureClippedBinary.png', captureClippedBinary)

        #類似度の検索
        if(self.UseImg == 'Canny'):
            musicImgForJudge = self.musicImgCanny
            playerImgForJudge = self.playerImgCanny
            captureClippedForJudge = captureClippedCanny
        else:
            musicImgForJudge = self.musicImgBinary
            playerImgForJudge = self.playerImgBinary
            captureClippedForJudge = captureClippedBinary

        musicMatch= cv2.matchTemplate(musicImgForJudge, captureClippedForJudge, cv2.TM_CCOEFF_NORMED)
        playerMatch = cv2.matchTemplate(playerImgForJudge, captureClippedForJudge, cv2.TM_CCOEFF_NORMED)
        mMinSim, mMaxSim, mMinLoc, mMaxLoc = cv2.minMaxLoc(musicMatch)
        pMinSim, pMaxSim, pMinLoc, pMaxLoc = cv2.minMaxLoc(playerMatch)

        if(IsItSimilar(pMaxSim) and IsItSimilar(mMaxSim)):
            print('Found(p=%g, m=%g' % (pMaxSim, mMaxSim))
            #母画像のクリップ（色付き）に序曲領域を描画
            captureClippedMarked = captureClipped.copy()
            top_left = pMaxLoc
            bottom_right = (top_left[0] + self.playerW, top_left[1] + self.playerH)
            cv2.rectangle(captureClippedMarked,top_left, bottom_right, 255, 2)
            #母画像のクリップ（色付き）にプレイヤー名領域を描画
            top_left = mMaxLoc
            bottom_right = (top_left[0] + self.musicW, top_left[1] + self.musicH)
            cv2.rectangle(captureClippedMarked,top_left, bottom_right, 255, 2)
            cv2.imwrite('tmp_captureClippedMarked(LastFound).png', captureClippedMarked)
            return True
        else:
            print('Not Found(p=%g, m=%g' % (pMaxSim, mMaxSim))
            #母画像のクリップ（色付き）に序曲領域を描画
            captureClippedMarked = captureClipped.copy()
            top_left = pMaxLoc
            bottom_right = (top_left[0] + self.playerW, top_left[1] + self.playerH)
            cv2.rectangle(captureClippedMarked,top_left, bottom_right, 255, 2)
            #母画像のクリップ（色付き）にプレイヤー名領域を描画
            top_left = mMaxLoc
            bottom_right = (top_left[0] + self.musicW, top_left[1] + self.musicH)
            cv2.rectangle(captureClippedMarked,top_left, bottom_right, 255, 2)
            cv2.imwrite('tmp_captureClippedMarked(LastNotFound).png', captureClippedMarked)
            return False

    def countDownTuan(self):
        self.isCountDown = True
        timeInitial = self.timeOverture * 3
        timeRemaining = timeInitial
        while(timeRemaining > self.timeOverture * 2):
            if(self.resetToken):
                self.reset()
                return
            timeElapsed = time.time() - self.startTime
            timeRemaining = timeInitial - timeElapsed

            if(timeRemaining < self.timeOverture * 2 +5 and timeRemaining > self.timeOverture * 2):
                freq = 440 # Set frequency To 2500 Hertz
                dur = 400 # Set duration To 1000 ms == 1 second
                winsound.Beep(freq, dur)     
            self.timerText.set('ready for Tuan: ' + str(int(timeRemaining - self.timeOverture * 2)))
            time.sleep(0.2)

        freq = 880 # Set frequency To 2500 Hertz
        dur = 600 # Set duration To 1000 ms == 1 second
        winsound.Beep(freq, dur)  

        while(timeRemaining > 0):
            if(self.resetToken):
                self.reset()
                return
            timeElapsed = time.time() - self.startTime
            timeRemaining = timeInitial - timeElapsed

            if(timeRemaining < 10 and timeRemaining > 0):
                freq = 1760 # Set frequency To 2500 Hertz
                dur = 400 # Set duration To 1000 ms == 1 second
                winsound.Beep(freq, dur)     
            self.timerText.set('overture remaining: ' + str(int(timeRemaining)))
            time.sleep(1.0)

        self.timerText.set('...')
        self.isCountDown = False

    def countDown(self):
        self.isCountDown = True
        timeInitial = self.timeOverture
        timeRemaining = timeInitial
        while(timeRemaining > 0):
            if(self.resetToken):
                self.reset()
                return
            timeElapsed = time.time() - self.startTime
            timeRemaining = timeInitial - timeElapsed

            if(timeRemaining < 10):
                freq = 1760 # Set frequency To 2500 Hertz
                dur = 400 # Set duration To 1000 ms == 1 second
                winsound.Beep(freq, dur)

            self.timerText.set('overture remaining:' + str(int(timeRemaining)))
            time.sleep(1.0)
        self.timerText.set('...')
        self.isCountDown = False
        
    def reset(self):
        
        time.sleep(2.0)
        self.resetToken = False
        self.isCountDown = False
        self.timerText.set('Reset.')

    def createWidget(self):
        #コントロール配置
        self.tuanBool = tk.BooleanVar()
        self.tuanBool.set(True)
        self.tuanCheckButton = tk.Checkbutton(self,variable=self.tuanBool, text='use Tuan?')
        self.tuanCheckButton.pack()
        self.buttonText = tk.StringVar()
        self.buttonText.set('*                     RESET COUNTDOWN                      *')
        self.resetButton = tk.Button(self, textvariable=self.buttonText, command=self.btClicked)
        self.resetButton.pack()
        self.labelText = tk.StringVar()
        self.labelText.set('Status message')
        self.stateLabel = tk.Label(self, textvariable=self.labelText)
        self.stateLabel.pack()
        self.timerText = tk.StringVar()
        self.timerText.set(self.username + '(' + str(self.timeOverture) + 'sec)')
        self.timerLabel = tk.Label(self, textvariable=self.timerText)
        self.timerLabel.pack()

def IsItSimilar(sim):
    if(sim > 0.80):
        return True
    else:
        return False

#
########################    int main(int argc, char** argv){} ******************************
#
if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()