import cv2
import os
import numpy as np
from numpy import interp
import random
import Parser
import imageio
# pip install pygifsicle
# sudo apt-get install gifsicle
from pygifsicle import optimize
#   SARIELI PROJECT
# This subproject works as a visualizer for KARA_AI
# It can animate 2D characters doing simple actions like:
# Talking, Blinking and just looking around
# WARNING: handle with care


# PS: FUNCTIONS MARKED WITH AN 'X' ONLY MODIFY THE NUMERICAL ARRAY 'ANIMATION' NOT THE FRAME ITSELF
# they just do math

cw = os.getcwd()

ADD_TEXT = True


class SylCharacter:

    def __init__(self, name):
        self.mouth = []
        self.eyes = []
        self.eyes_m = []
        self.head = []
        char = cw + '/' + name  # default
        files = os.listdir(char)
        size = cv2.imread(char + '/c0001.png', -1).shape[1], cv2.imread(char + '/c0001.png', -1).shape[0]
        readmode = cv2.IMREAD_LOAD_GDAL
        for file in files:
            if '.png' in file:
                if 'ba' in file:
                    mg = cv2.resize(cv2.imread(char + '/' + file, readmode), size, interpolation=cv2.INTER_LINEAR)
                    self.eyes_m.append(mg)
                elif 'b' in file and not 'ba' in file:
                    mg = cv2.resize(cv2.imread(char + '/' + file, readmode), size, interpolation=cv2.INTER_LINEAR)
                    self.eyes.append(mg)
                elif 'a' in file:
                    mg = cv2.resize(cv2.imread(char + '/' + file, readmode), size, interpolation=cv2.INTER_LINEAR)
                    self.mouth.append(mg)
                if 'c' in file:
                    image = cv2.imread(char + '/' + file, readmode)
                    trans_mask = image[:, :, 3] == 0
                    image[trans_mask] = [255,255,255,255]
                    self.head.append(image)

    def save(self, frames):
        x = 0
        min_size = [10000, 10000]
        for frame in frames:
            cv2.imwrite(os.getcwd()+"\\imgs\\"+str(x)+".png", frame)
            if frame.shape[0] < min_size[1]:
                min_size[1] = frame.shape[0]
            if frame.shape[1] < min_size[0]:
                min_size[0] = frame.shape[1]
            x += 1
        with imageio.get_writer(os.getcwd()+"\\static\\"+"last.gif", mode="I", loop=1) as writer:
            for idx, frame in enumerate(frames):
                print("Adding frame to GIF file: ", idx + 1)
                writer.append_data(cv2.cvtColor(cv2.resize(frame, min_size, interpolation=cv2.INTER_LINEAR), cv2.COLOR_BGR2RGB))
        optimize(os.getcwd()+"\\static\\"+"last.gif")

    def change_char(self, ch):
        char = cw + '/' + ch
        files = os.listdir(char)
        size = [0,0]
        size[0] = cv2.imread(char + '/c0000').shape[0]
        size[1] = cv2.imread(char + '/c0000').shape[1]
        for file in files:
            if '.png' in file:
                if 'ba' in file:
                    mg = cv2.resize(cv2.imread(char+'/'+file, -1), size, interpolation=cv2.INTER_LINEAR)
                    self.eyes_m.append(cv2.imread(char+'/'+file, -1))
                elif 'b' in file and not 'ba' in file:
                    mg = cv2.resize(cv2.imread(char+'/'+file, -1), size, interpolation=cv2.INTER_LINEAR)
                    self.eyes.append(cv2.imread(char+'/'+file, -1))
                elif 'a' in file:
                    mg = cv2.resize(cv2.imread(char+'/'+file, -1), size, interpolation=cv2.INTER_LINEAR)
                    self.mouth.append(cv2.imread(char+'/'+file, -1))
                if 'c' in file:
                    self.head.append(cv2.imread(char+'/'+file))
        return 1

    def layer(self, s_img, l_img, off=0):
        # this WILL modify l_img, so make sure to make a copy if ya need it
        # Can you tell I wrote this a year later?
        x_offset = 0
        y_offset = 0
        rows, cols, _ = s_img.shape
        M = np.float32([[1, 0, off], [0, 1, 0]])
        s_img = cv2.warpAffine(s_img, M, (cols, rows))
        if s_img.shape[2] != 4:
            l_img[y_offset:y_offset+s_img.shape[0], x_offset:x_offset+s_img.shape[1]] = s_img
            return l_img
        y1, y2 = 0, s_img.shape[0]
        x1, x2 = 0, s_img.shape[1]

        alpha_s = s_img[:, :, 3] / 255.0
        alpha_l = 1.0 - alpha_s

        for c in range(0, 3):
            l_img[y1:y2, x1:x2, c] = (alpha_s * s_img[:, :, c] +
                                      alpha_l * l_img[y1:y2, x1:x2, c])

        return l_img

    def layer_nomorph(self, s_img, l_img,off=0):
        # this WILL modify l_img, so make sure to make a copy if ya need it
        # Can you tell I wrote this a year later?
        x_offset = off
        y_offset = 0
        rows, cols, _ = s_img.shape
        if s_img.shape[2] != 4:
            l_img[y_offset:y_offset+s_img.shape[0], x_offset:x_offset+s_img.shape[1]] = s_img
            return l_img
        y1, y2 = y_offset, s_img.shape[0]
        x1, x2 = x_offset, s_img.shape[1]+x_offset

        alpha_s = s_img[:, :, 3] / 255.0
        alpha_l = 1.0 - alpha_s
        if l_img.shape[2] != 4:
            i = 0
            for c in range(0, 3):
                l_img[y_offset:y_offset+s_img.shape[0], x_offset:x_offset+s_img.shape[1], i] = (alpha_s * s_img[:, :, c] +
                                          l_img[y1:y2, x1:x2, i])
                i += 1
                if i > 2:
                    i = 2
        for c in range(0, 3):
            l_img[y_offset:y_offset+s_img.shape[0], x_offset:x_offset+s_img.shape[1], c] = (alpha_s * s_img[:, :, c] +
                                      alpha_l * l_img[y1:y2, x1:x2, c])

        return l_img

    def join(self,h_ind,m_ind,e_ind, off=0):
        now = np.full(self.head[h_ind].shape, 255,dtype=np.uint8)
        now = self.layer(self.head[h_ind],now,off=off)
        now = self.layer(self.eyes[e_ind],now,off=off)
        now = self.layer(self.mouth[m_ind],now,off=off)
        return now

    def render_frame(self, h, m, e, r, off=0):
        h_m = len(self.head)-1
        e_m = len(self.eyes)-1
        m_m = len(self.mouth)-1
        ht = int(interp(h, [0, 5], [0, h_m]))
        et = int(interp(e, [0, 5], [0, e_m]))
        mt = int(interp(m, [0, 5], [0, m_m]))
        if r == 5:
            return self.join(ht, mt, et, off=off)
        elif r == 4:
            return self.move_eyes(ht, mt, e)
        else:
            return self.join(ht, mt, et)

    # frames may not actually be connected with eachother, so using this would probably cause problems
    # ex: [Mouth_open] -> [Mouth_closed] -> [Mouth_smile], Mouth_smile is not the avarage of Mouth_open and Mouth_closed
    # def smooth_process(animation):
    #    full = []
    #    i = 0
    #    for i in range(len(animation)):
    #        frame = animation[i]
    #        full.append(frame)
    #        if i+1 < len(animation)-1:
    #            tmp = animation[i+1]
    #            w = [frame[0]+tmp[0]//2,frame[1]+tmp[1]//2,frame[2]+tmp[2]//2]
    #            full.append(w)
    #        i = i + 1
    #    return full

    def add_text(self,render, where, text):
        i = 0
        scr = ""
        for frame in render[where:]:
            if i < len(text):
                char = text[i]
                if char != "/":
                    scr += char
                i = i + 1
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(frame,scr,(20,650), font, 0.4,(0,0,0,255),5,cv2.FILLED)
            cv2.putText(frame,scr,(20,650), font, 0.4,(255,255,255,255),1,cv2.FILLED)

            render[where+i] = frame
        return render, i

    def render_animation(self,an):
        # if smooth:
        #    an = smooth_process(animation)
        # else:
        #    an = animation
        i = 0
        render = []
        print('rendering')
        for frame in an:
            if len(frame) == 5:
                f = self.render_frame(frame[0],frame[1],frame[2],len(frame),frame[4])
            else:
                f = self.render_frame(frame[0],frame[1],frame[2],len(frame))
            render.append(f)
            print(frame)
        return render

    # good enough
    def say(self,text,slow=0,loud=0): #x
        vocals = ['u','o','i','e','a']
        syl = []
        w = False
        last = ''
        test_text = ""
        for char in text:
            test_text += char
            if char.lower() in vocals:
                w = True
                last = char
            elif char == " " or char == ",":
                if slow != 0:
                    for i in range(slow):
                        vocal = vocals.index(last.lower())+1+loud
                        if vocal > len(vocals):
                            vocal = len(vocals)
                        syl.append(vocal)
                        test_text += '/'
                w = False
                syl.append(0)
            elif not w:
                syl.append(0)
            if w:
                vocal = vocals.index(last.lower())+1+loud
                if vocal > len(vocals):
                    vocal = len(vocals)
                syl.append(vocal)
        animation = [[0,0,0]]
        for s in syl:
            animation.append([0,s,0])
        animation.append([0,0,0])
        print(syl)
        return animation, test_text

    def mouthopen(self, animation, where, x, fr):
        i = 0
        for frm in animation[where:where+fr]:
            frm[1] = 5
            animation[i] = frm
        return animation

    def nothing(self, animation, lng):
        for i in range(lng):
            animation.append([0,0,0])
        return animation

    # this can be made into something better
    def random_blinks(self,animation, am): #x
        for i in range(am):
            where = random.randint(1,len(animation)-3)
            animation[where-1][2] = 3
            animation[where][2] = 5
            animation[where+1][2] = 3
        return animation
    def add_moving_eyes(self,animation,ind,x, long): #x
        for i in range(long):
            h,m,e = animation[ind+i][:3]
            animation[ind+i] = [h,m,x,0]
        return animation
    def vibrate(self,animation, ind, x,long=3):
        S = x
        for i in range(long):
            if ind+i > len(animation)-1:
                return animation
            h,m,e = animation[ind+i][:3]
            animation[ind+i] = [h,m,e,0,S]
            if S == x:
                S = 0
            else:
                S = x
        return animation
    def move_eyes(self,h_ind,m_ind,e_ind):
        #ugh, this is a headache
        now = np.full(self.head[h_ind].shape, 255,dtype=np.uint8)
        now = self.layer(self.head[h_ind],now)
        now = self.layer(self.mouth[m_ind],now)
        if e_ind > len(self.eyes_m)-1:
            e_ind = len(self.eyes_m)-1
        now = self.layer(self.eyes_m[e_ind],now)

        return now

    actions = {
        'shivers':[vibrate],
        'looks':[add_moving_eyes],
        'ignores':[add_moving_eyes],
        'gasps':[mouthopen],
        'yells':[mouthopen, vibrate],
        'screams':[mouthopen, vibrate]
        }

    def splittext(self,text, n=25):
        splot = text.split(" ")
        new = [""]
        i = 0
        done = True
        ii = 0
        while True:
            for word in splot[ii:]:
                new[i] += " "+word
                done = True
                ii += 1
                if len(new[i]) > n:
                    i += 1
                    new.append("")
                    done = False
                    break
                if word.endswith('_'):
                                    i += 1
                                    new.append("")
                                    done = False
                                    break
            if done or len(splot[ii:]) == 0:
                break
        return new

    def use_parser(self,text):
        allframes = []
        ch = Parser.character('Maho')
        parsed = ch.get_actions(text)
        who = parsed[1]

        if len(text) > 60:
            slices = self.splittext(text.replace(who+": ", ""))
            for i in range(len(slices)):
                slices[i] = who+": " + slices[i]
                if i != len(slices)-1:
                    print(slices)
                    try:
                        slices[i] = slices[i] + " *She " + parsed[2][0] + "*"
                    except TypeError:
                        continue
        else:
            slices = [text]
        for inps in slices:
            texts = inps.replace("_", "")
            parsed = ch.get_actions(texts)
            if parsed[0] in ['yell', 'scream', 'shout']:
                anim = self.say(parsed[0], loud=2)[0]
            anim = self.say(parsed[0])[0]
            anim = self.random_blinks(anim,int((len(anim)-1)*0.10))
            if "_" in inps:
                anim = self.nothing(anim, 5)
            print(parsed)
            if parsed[2] != None:
                for act in parsed[2]:
                    if act in self.actions:
                        for func in self.actions[act]:
                            anim = func(self,anim, 0, 1, len(anim))

            frames = self.render_animation(anim)
            tosay = parsed[0]
            if ADD_TEXT:
                frames = self.add_text(frames, 0, tosay)[0]

            allframes += frames
        return allframes
