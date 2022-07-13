from kivy.app import App
from kivy.lang.builder import Builder
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.animation import Animation
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import NumericProperty , ObjectProperty
from asynckivy import start , sleep
from random import shuffle
from sqlite3 import connect
from os import chdir , path
class Win_Popup(Popup):
    pass
class Loss_Popup(Popup) :
    pass
class Winner(Popup):
    pass
class Matcher_Data(Label) :
    def __init__(self,**kwargs):
        super(Matcher_Data,self).__init__(**kwargs)
        self.size_hint_y=None
        self.font_size=self.height*.8
class Matchers_Popup(Popup):
    def __init__(self,**kwargs):
        super(Matchers_Popup,self).__init__(**kwargs)
        self.auto_dismiss=False
        self.title='Matchers'
        self.title_size=self.height*.2
        self.title_align='center'
        self.box_layout=BoxLayout(orientation='vertical',padding=self.width*.1)
        self.grid_layout=GridLayout(rows=16,cols=3)
        self.button=Button(text='Close',size_hint=(.4,.08),pos_hint={'center_x':.5},on_release=self.dismiss)
        self.button.font_size=self.button.height*.3
        self.grid_layout.spacing=self.grid_layout.width*.04
        self.grid_layout.add_widget(Matcher_Data(text="Matcher",color=(1,1,0,1),bold=True,underline=True,height=self.grid_layout.height*.3))
        self.grid_layout.add_widget(Matcher_Data(text="Score",color=(0,1,0,1),bold=True,underline=True,height=self.grid_layout.height*.3))
        self.grid_layout.add_widget(Matcher_Data(text="Moves",color=(1,.1,.1,1),bold=True,underline=True,height=self.grid_layout.height*.3))
        self.box_layout.add_widget(self.grid_layout)
        self.box_layout.add_widget(self.button)
        self.add_widget(self.box_layout)
class Card(Button):
    pass
class Game(App):
    previous = ObjectProperty()
    nclick = NumericProperty()
    done=NumericProperty()
    speed=NumericProperty()
    moves=NumericProperty()
    score=NumericProperty()
    total_score=NumericProperty()
    total_moves=NumericProperty()
    def build(self) :
        chdir(path.dirname(path.abspath(__file__)))
        self.button_click = SoundLoader().load('audio/button_click.wav')
        self.card_click = SoundLoader().load('audio/click.wav')
        self.disappear = SoundLoader().load('audio/disappear.wav')
        self.score_up = SoundLoader().load('audio/score_up.wav')
        self.db = connect('database/matchers.db')
        self.cr = self.db.cursor()
        self.cr.execute('SELECT * FROM options')
        data = self.cr.fetchone()
        self.switch_audio(data[0])
        self.change_background(data[1])
        return Builder.load_file('design.kv')
    async def restart(self) :
        self.shuffle_cards()
        self.root.ids.progress.value=0
        anime = Animation(value=100,duration=10-self.speed)
        self.root.ids.replay.disabled=True
        for card in self.root.ids.cards.children :
            card.background_color=1,1,1,1
        await sleep(.1)
        anime.start(self.root.ids.progress)
        await sleep(10-self.speed)
        self.clear_cards()
        await sleep(.1)
        self.root.ids.replay.disabled=False
        for card in self.root.ids.cards.children :
            card.disabled=False
        self.anime= Animation(value=0,duration=15-self.speed)
        await sleep(.1)
        self.anime.start(self.root.ids.progress)
        await sleep(15-self.speed)
        Loss_Popup().open()
    def on_start(self):
        for _ in range(16) :
            self.root.ids.cards.add_widget(Card())
    def check_correct(self,clicked) :
        if clicked.background_normal!=self.previous.background_normal :
            self.disappear.play()
            self.clear_anime.start(clicked)
            self.clear_anime.start(self.previous)
            self.moves+=1
        elif clicked is self.previous :
            self.disappear.play()
            self.clear_anime.start(clicked)
        else :
            self.score_up.play()
            self.done+=1
            self.moves+=1
            self.score+=5
            self.previous.disabled=clicked.disabled=True
        if self.done//8 :
            self.task.cancel()
            self.anime.cancel(self.root.ids.progress)
            Win_Popup().open()
    def clear_cards(self) :
        self.clear_anime= Animation(background_color=(0,0,0,1),duration=.2)
        for card in self.root.ids.cards.children :
            self.clear_anime.start(card)
    def shuffle_cards(self) :
        images = list(range(8))*2
        shuffle(images)
        for card , image in zip(self.root.ids.cards.children , images) :
            card.disabled=True
            card.background_disabled_normal = card.background_normal = f'images/{image}.png'
    def replay(self) :
        self.previous=ObjectProperty()
        self.nclick=self.done=self.score=self.moves=0
        self.task.cancel()
        self.anime.cancel(self.root.ids.progress)
        self.task=start(self.restart())
    def start_but(self) :
        self.total_score=self.total_moves=self.score=self.moves=self.speed=self.nclick=self.score=self.moves=self.done=0
        self.previous=ObjectProperty()
        self.root.ids.replay.disabled=True
        self.task = start(self.restart())
    def finish(self) :
        self.cr.execute('SELECT * FROM matchers ORDER BY score DESC,moves')
        highest_row=self.cr.fetchone()
        try :
            if self.total_score+self.score>highest_row[1] or self.total_score+self.score==highest_row[1] and self.total_moves+self.moves<highest_row[2]:
                Winner().open()
            else :
                self.total_score=self.total_moves=self.score=self.moves=0
                self.root.ids.progress.value=0
        except TypeError :
            if self.score+self.total_score :
                Winner().open()
        for card in self.root.ids.cards.children :
            card.disabled=True
            card.background_color=0,0,0,1
        self.root.ids.start.disabled=False
        self.root.ids.replay.disabled=True
        for card in self.root.ids.cards.children :
            card.disabled=True
    def save_score(self,name,score,moves) :
        self.cr.execute('SELECT * FROM matchers ORDER BY score DESC,moves')
        matchers = self.cr.fetchall()
        if name in sum(matchers,()) :
            self.cr.execute(f'UPDATE matchers SET score={score}, moves={moves} where name="{name}"')
        else :
            if len(matchers) == 15:
                self.cr.execute('DELETE FROM matchers LIMIT 1 OFFSET 14')
            self.cr.execute('INSERT INTO matchers values(?,?,?)',(name,score,moves))
        self.db.commit()
    def show_matchers(self) :
        self.matchers_popup=Matchers_Popup()
        self.matchers_popup.button.on_release=self.button_click.play
        self.Board= self.matchers_popup.grid_layout
        self.cr.execute('SELECT * FROM matchers ORDER BY score DESC,moves')
        for matcher in self.cr.fetchall() :
            self.Board.add_widget(Matcher_Data(text=matcher[0],height=self.Board.height*.3))
            self.Board.add_widget(Matcher_Data(text=f'{matcher[1]}',height=self.Board.height*.3))
            self.Board.add_widget(Matcher_Data(text=f'{matcher[2]}',height=self.Board.height*.3))
    def change_background(self,color) :
        if color=='Blue' :
            Window.clearcolor=0,0,1,1
        elif color=='Brown':
            Window.clearcolor=.427,0.125,0,1
        else :
            Window.clearcolor=1,1,1,1
        self.cr.execute(f'UPDATE options SET background="{color}"')
        self.db.commit()
    def switch_audio(self,audio) :
        self.button_click.volume = audio
        self.card_click.volume = audio
        self.disappear.volume = audio
        self.score_up.volume = audio
        return bool(audio)
    def state(self):
        self.cr.execute('SELECT * FROM options')
        back = self.cr.fetchone()
        return back[0],back[1]
if __name__=='__main__':
    Game().run()
