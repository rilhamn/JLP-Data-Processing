from tkinter import *
from tkinter import ttk
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
NavigationToolbar2Tk)

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from matplotlib.figure import Figure
from statistics import mean
from scipy.stats import linregress
import math
import re
import datetime
from pulp import LpMaximize, LpMinimize, LpProblem, LpStatus, LpVariable

import os
path="D:\Pribadi\Materi Belajar\Materi Magang\PT Medco Power Indonesia\modelling\ijen modelling\Python Testing\JLP"
os.chdir(path)
current_directory = os.getcwd()
#===================================== FUNCTION READ AND CLEAN =======================================#
def read_and_clean(file_name,type):
    df=pd.read_excel(file_name,parse_dates=["time"])
    if type=="JLP":
        df["whp"]=df["whp"].apply(lambda x:float(x))
        df["lip_pressure"]=df["lip_pressure"].apply(lambda x:float(x))
        df["weirbox"]=df["weirbox"].apply(lambda x:float(x))
    elif type=="TFT":
        df["enthalpy"]=df["enthalpy"].apply(lambda x:float(x))
        df["massrate"]=df["massrate"].apply(lambda x:float(x))
    return df

#======================================= FUNCTION JLP PROCESSING =======================================#
def processing_jlp():
    # read
    global df_jlp
    df_jlp=read_and_clean(input_jlp.get(),"JLP")
    # cali
    cali_lip=0
    cali_weir=0
    df_jlp["lip_pressure"]=df_jlp["lip_pressure"].apply(lambda x: x+cali_lip)
    df_jlp["weirbox"]=df_jlp["weirbox"].apply(lambda x: x+cali_weir)
    # Watm
    df_jlp["watm"]=df_jlp["weirbox"].apply(lambda x: 4720*(pow(x*0.01,2.5)).real)
    # Lip Pressure to bara
    df_jlp["lip_pressure_bara"]=df_jlp["lip_pressure"].apply(lambda x:(x/14.5)+float(input_atm_pressure.get()))
    # Area
    global area
    area=0.25*math.pi*(float(input_id.get())**2)
    # Y
    df_jlp["y"]=df_jlp[["watm","lip_pressure_bara"]].apply(lambda x: x["watm"]/(area*(x["lip_pressure_bara"]**0.96)),axis=1)
    # H
    df_jlp["enthalpy"]=df_jlp["y"].apply(lambda x: (float(input_atm_enthalpy_vapor.get())+(925*x))/(1+(7.85*x)))
    # M
    df_jlp["massrate"]=df_jlp[["watm","enthalpy"]].apply(lambda x:((x["watm"]*(float(input_atm_enthalpy_vapor.get())-float(input_atm_enthalpy_liquid.get())))/(float(input_atm_enthalpy_vapor.get())-x["enthalpy"]))/3.6,axis=1)


def processing_jlp_calibration():
    # read
    global df_jlp_calibrated
    df_jlp_calibrated=df_jlp.copy()
    df_jlp_calibrated.drop(columns=["watm","lip_pressure_bara","y","enthalpy","massrate"])

    # cali
    cali_lip=input_jlp_calibration.get()
    cali_weir=input_weir_calibration.get()
    df_jlp_calibrated["lip_pressure"]=df_jlp_calibrated["lip_pressure"].apply(lambda x:x+float(cali_lip))
    df_jlp_calibrated["weirbox"]=df_jlp_calibrated["weirbox"].apply(lambda x:x+float(cali_weir))
    # Watm
    df_jlp_calibrated["watm"]=df_jlp_calibrated["weirbox"].apply(lambda x: 4720*(pow(x*0.01,2.5)).real)
    # Lip Pressure to bara
    df_jlp_calibrated["lip_pressure_bara"]=df_jlp_calibrated["lip_pressure"].apply(lambda x:(x/14.5)+float(input_atm_pressure.get()))
    # Area
    global area
    area=0.25*math.pi*(float(input_id.get())**2)
    # Y
    df_jlp_calibrated["y"]=df_jlp_calibrated[["watm","lip_pressure_bara"]].apply(lambda x: x["watm"]/(area*(x["lip_pressure_bara"]**0.96)),axis=1)
    # H
    df_jlp_calibrated["enthalpy"]=df_jlp_calibrated["y"].apply(lambda x: (float(input_atm_enthalpy_vapor.get())+(925*x))/(1+(7.85*x)))
    # M
    df_jlp_calibrated["massrate"]=df_jlp_calibrated[["watm","enthalpy"]].apply(lambda x:((x["watm"]*(float(input_atm_enthalpy_vapor.get())-float(input_atm_enthalpy_liquid.get())))/(float(input_atm_enthalpy_vapor.get())-x["enthalpy"]))/3.6,axis=1)

def processing_tft():
    global df_tft
    df_tft=read_and_clean(input_tft.get(),"TFT")

#======================================== FUNCTION SHOW GRAPH ==========================================#
#Funtion Plot JLP and TFT
def plot():
    if var_jlp.get()=="hour":
        fig = Figure(figsize=(7,5))
        ax1 = fig.add_subplot(111)
        ax1.plot(df_jlp["time"],df_jlp["enthalpy"],color="royalblue",alpha=0.7)
        if df_tft.empty:
            pass
        else:
            ax1.scatter(df_tft["time"],df_tft["enthalpy"],color="indigo")
        ax1.set_title("M and H Every Measurement Time Point",fontsize=12)
        ax1.xaxis.set_tick_params(rotation=45,labelsize=6)
        ax1.yaxis.set_tick_params(labelsize=6)
        ax1.set_ylabel("H (kJ/kg)",fontsize=8)
        ax2 = ax1.twinx()
        ax2.plot(df_jlp["time"],df_jlp["massrate"],color="orange",alpha=0.7)
        ax2.yaxis.set_tick_params(labelsize=6)
        ax2.set_ylabel("M (kg/s)",fontsize=8)
        if df_tft.empty:
            pass
        else:
            ax2.scatter(df_tft["time"],df_tft["massrate"],color="red")
        
    else:
        df_jlp_group=df_jlp.copy()
        df_jlp_group.insert(1,"hour",df_jlp_group["time"].dt.strftime("%H").astype(int))
        df_jlp_group.insert(1,"date",df_jlp_group["time"].dt.strftime("%d").astype(int))
        df_jlp_group.insert(1,"month",df_jlp_group["time"].dt.month)
        df_jlp_group.insert(1,"year",df_jlp_group["time"].dt.year)

        fig = Figure(figsize=(7,5))
        ax1 = fig.add_subplot(111)

        if var_jlp.get()=="date":
            time_filter=["year","month","date"]
        elif var_jlp.get()=="month":
            time_filter=["year","month"]
        elif var_jlp.get()=="year":
            time_filter=["year"]

        df_jlp_group=df_jlp_group.groupby(time_filter).mean()
        df_jlp_group=df_jlp_group.reset_index()

        loop=0
        for i in time_filter:
            if loop==0:
                df_jlp_group["time"]=df_jlp_group[i].apply(lambda x:str(x))
            else:
                df_jlp_group["time"]=df_jlp_group[["time",i]].apply(lambda x:str(x["time"])+"-"+str(x[i]),axis=1)
            loop=+1
        
        ax1.plot(df_jlp_group["time"],df_jlp_group["enthalpy"],color="royalblue",marker='*',markersize=6)
        ax1.set_title(f"Average M and H, Grouped by {var_jlp.get().capitalize()}",fontsize=12)
        ax1.xaxis.set_tick_params(rotation=45,labelsize=6)
        ax1.yaxis.set_tick_params(labelsize=6)
        ax1.set_ylabel("H (kJ/kg)",fontsize=8)
        ax2 = ax1.twinx()
        ax2.plot(df_jlp_group["time"],df_jlp_group["massrate"],color="orange",marker='*',markersize=6)
        ax2.yaxis.set_tick_params(labelsize=6)
        ax2.set_ylabel("M (kg/s)",fontsize=8)

    ax1.legend(["H - JLP","H - TFT"],loc="upper left")
    ax2.legend(["M - JLP","M - TFT"],loc="upper right")

    canvas=FigureCanvasTkAgg(fig,label_showgraph_tab_1)
    canvas.draw()
    canvas.get_tk_widget().grid(row=1,column=0,rowspan=30,columnspan=1000,padx=10,pady=10,sticky=N)
    toolbar=NavigationToolbar2Tk(canvas,label_showgraph_tab_1,pack_toolbar=False)
    toolbar.update()
    toolbar.grid(row=40,column=0,rowspan=1,columnspan=1000,padx=10,pady=10,sticky=W)

def plot_caliberated():
    if var_jlp_calibrated.get()=="hour":
        fig = Figure(figsize=(7,5))
        ax1 = fig.add_subplot(111)
        ax1.plot(df_jlp_calibrated["time"],df_jlp_calibrated["enthalpy"],color="royalblue",alpha=0.7)
        if df_tft.empty:
            pass
        else:
            ax1.scatter(df_tft["time"],df_tft["enthalpy"],color="indigo")
        ax1.set_title("M and H Every Measurement Time Point",fontsize=12)
        ax1.xaxis.set_tick_params(rotation=45,labelsize=6)
        ax1.yaxis.set_tick_params(labelsize=6)
        ax1.set_ylabel("H (kJ/kg)",fontsize=8)
        ax2 = ax1.twinx()
        ax2.plot(df_jlp_calibrated["time"],df_jlp_calibrated["massrate"],color="orange",alpha=0.7)
        ax2.yaxis.set_tick_params(labelsize=6)
        ax2.set_ylabel("M (kg/s)",fontsize=8)
        if df_tft.empty:
            pass
        else:
            ax2.scatter(df_tft["time"],df_tft["massrate"],color="red")
    else:
        df_jlp_group=df_jlp_calibrated.copy()
        df_jlp_group.insert(1,"hour",df_jlp_group["time"].dt.strftime("%H").astype(int))
        df_jlp_group.insert(1,"date",df_jlp_group["time"].dt.strftime("%d").astype(int))
        df_jlp_group.insert(1,"month",df_jlp_group["time"].dt.month)
        df_jlp_group.insert(1,"year",df_jlp_group["time"].dt.year)

        fig = Figure(figsize=(7,5))
        ax1 = fig.add_subplot(111)

        if var_jlp_calibrated.get()=="date":
            time_filter=["year","month","date"]
        elif var_jlp_calibrated.get()=="month":
            time_filter=["year","month"]
        elif var_jlp_calibrated.get()=="year":
            time_filter=["year"]

        df_jlp_group=df_jlp_group.groupby(time_filter).mean()
        df_jlp_group=df_jlp_group.reset_index()

        loop=0
        for i in time_filter:

            if loop==0:
                df_jlp_group["time"]=df_jlp_group[i].apply(lambda x:str(x))
            else:
                df_jlp_group["time"]=df_jlp_group[["time",i]].apply(lambda x:str(x["time"])+"-"+str(x[i]),axis=1)
            loop=+1
        
        ax1.plot(df_jlp_group["time"],df_jlp_group["enthalpy"],color="royalblue",marker='*',markersize=6)
        ax1.xaxis.set_tick_params(rotation=45,labelsize=6)
        ax1.yaxis.set_tick_params(labelsize=6)
        ax1.set_ylabel("H (kJ/kg)",fontsize=8)
        ax2 = ax1.twinx()
        ax2.plot(df_jlp_group["time"],df_jlp_group["massrate"],color="orange",marker='*',markersize=6)
        ax2.yaxis.set_tick_params(labelsize=6)
        ax2.set_ylabel("M (kg/s)",fontsize=8)

    ax1.legend(["H - JLP","H - TFT"],loc="upper left")
    ax2.legend(["M - JLP","M - TFT"],loc="upper right")

    canvas=FigureCanvasTkAgg(fig,label_showgraph_tab_2)
    canvas.draw()
    canvas.get_tk_widget().grid(row=1,column=0,rowspan=30,columnspan=1000,padx=10,pady=10,sticky=N)
    toolbar=NavigationToolbar2Tk(canvas,label_showgraph_tab_2,pack_toolbar=False)
    toolbar.update()
    toolbar.grid(row=40,column=0,rowspan=1,columnspan=1000,padx=10,pady=10,sticky=W)

#====================================== FUNCTION OPTIMIZATION ======================================#
## SOMEONE HELP ME!!

#====================================== FUNCTION SAVE FILE =========================================#
def save_xlsx():
    with pd.ExcelWriter(f"{input_save.get()}.xlsx") as writer:
        df_jlp_calibrated.to_excel(writer,"JLP Calibrated")

#================================ INTIAL CONDITION AND PROCESS =====================================#
df_jlp=pd.DataFrame()
df_jlp_calibrated=pd.DataFrame()
df_tft=pd.DataFrame()
area=0

root=Tk()
root.title("JLP Raw Data Processing")
root.config(background="white")
root.geometry("1080x740")
root.resizable(False, False)

label_creator=Label(root,text="Created by Ilham Narendrodhipo as part of internship project in Medco Cahaya Geothermal")
label_creator.grid(row=500,column=0,columnspan=3,padx=3,pady=2,sticky=SW)
label_creator.config(font=("HP Simplified",8),background="white")

# Tab
header_style = ttk.Style()
header_style.theme_create( "headerstyle", parent="alt", settings={
        "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0],"background":"white"}},
        "TNotebook.Tab": {"configure": {"padding": [20,10],"background":"white","font":["HP Simplified",12]}}})
header_style.theme_use("headerstyle")
notebook = ttk.Notebook(root,width=1070,height=660)

page_style= ttk.Style()
page_style.configure("pagestyle.TFrame", background="white")
tab_1 = ttk.Frame(notebook,style="pagestyle.TFrame")
tab_2 = ttk.Frame(notebook,style="pagestyle.TFrame")
tab_3 = ttk.Frame(notebook,style="pagestyle.TFrame")

notebook.add(tab_1,text="A. JLP and TFT")
notebook.add(tab_2,text="B. JLP Calibration")
notebook.add(tab_3, text="C. Save File")
notebook.grid(row=1,column=0,columnspan=100,rowspan=20,padx=3,pady=2,sticky=NW)

## Tab_1 GUI
###
label_jlp_title=Label(tab_1,text="JLP Processing")
label_jlp_title.grid(row=0,column=0,columnspan=3,padx=3,pady=2,sticky=W)
label_jlp_title.config(font=("HP Simplified bold",12),background="white")
label_jlp=Label(tab_1,text="Raw Data Name:                  ")
label_jlp.grid(row=1,column=0,columnspan=1,padx=3,pady=2,sticky=W)
label_jlp.config(font=("HP Simplified",11),background="white")
input_jlp=Entry(tab_1,width=16,relief=SOLID)
input_jlp.grid(row=1,column=1,columnspan=2,padx=3,pady=2,sticky=E)
input_jlp.config(font=("HP Simplified",10),background="white")
label_id=Label(tab_1,text="Inside Diameter (cm):        ")
label_id.grid(row=2,column=0,columnspan=1,padx=3,pady=2,sticky=W)
label_id.config(font=("HP Simplified",11),background="white")
input_id=Entry(tab_1,width=16,relief=SOLID)
input_id.grid(row=2,column=1,columnspan=2,padx=3,pady=2,sticky=E)
input_id.config(font=("HP Simplified",10),background="white")
label_atm_pressure=Label(tab_1,text="Atm. Pressure:          ")
label_atm_pressure.grid(row=3,column=0,columnspan=1,padx=3,pady=2,sticky=W)
label_atm_pressure.config(font=("HP Simplified",11),background="white")
input_atm_pressure=Entry(tab_1,width=16,relief=SOLID)
input_atm_pressure.grid(row=3,column=1,columnspan=2,padx=3,pady=2,sticky=E)
input_atm_pressure.config(font=("HP Simplified",10),background="white")
label_atm_enthalpy_vapor=Label(tab_1,text="Atm. Enthalpy Vapor (kJ/kg):    ")
label_atm_enthalpy_vapor.grid(row=4,column=0,columnspan=1,padx=3,pady=2,sticky=W)
label_atm_enthalpy_vapor.config(font=("HP Simplified",11),background="white")
input_atm_enthalpy_vapor=Entry(tab_1,width=16,relief=SOLID)
input_atm_enthalpy_vapor.grid(row=4,column=1,columnspan=2,padx=3,pady=2,sticky=E)
input_atm_enthalpy_vapor.config(font=("HP Simplified",10),background="white")
label_atm_enthalpy_liquid=Label(tab_1,text="Atm. Enthalpy Liquid (kJ/kg):    ")
label_atm_enthalpy_liquid.grid(row=5,column=0,columnspan=1,padx=3,pady=2,sticky=W)
label_atm_enthalpy_liquid.config(font=("HP Simplified",11),background="white")
input_atm_enthalpy_liquid=Entry(tab_1,width=16,relief=SOLID)
input_atm_enthalpy_liquid.grid(row=5,column=1,columnspan=2,padx=3,pady=2,sticky=E)
input_atm_enthalpy_liquid.config(font=("HP Simplified",10),background="white")
button_excute_jlp=Button(tab_1,text="Execute",command=processing_jlp)
button_excute_jlp.grid(row=6,column=2,columnspan=1,padx=3,pady=2,sticky=E)
button_excute_jlp.config(font=("HP Simplified",9),background="white")
###
spacer1 = Label(tab_1, text="",background="white")
spacer1.grid(row=7, column=0)
label_tft_title=Label(tab_1,text="TFT")
label_tft_title.grid(row=8,column=0,columnspan=3,padx=3,pady=2,sticky=W)
label_tft_title.config(font=("HP Simplified bold",12),background="white")
label_tft=Label(tab_1,text="Raw Data Name:                  ")
label_tft.grid(row=9,column=0,columnspan=1,padx=3,pady=2,sticky=W)
label_tft.config(font=("HP Simplified",11),background="white")
input_tft=Entry(tab_1,width=16,relief=SOLID)
input_tft.grid(row=9,column=1,columnspan=2,padx=3,pady=2,sticky=E)
input_tft.config(font=("HP Simplified",10),background="white")
button_excute_tft = Button(tab_1,text="Execute",command=processing_tft)
button_excute_tft.grid(row=10,column=2,columnspan=1,padx=3,pady=2,sticky=E)
button_excute_tft.config(font=("HP Simplified",9),background="white")
###
spacer1 = Label(tab_1, text="",background="white")
spacer1.grid(row=0,column=4)
label_showgraph_tab_1=LabelFrame(tab_1,text="Before JLP Calibration",height=640,width=722)
label_showgraph_tab_1.grid(row=0,column=5,rowspan=1000,columnspan=1000,padx=3,pady=2,sticky=NW)
label_showgraph_tab_1.config(font=("HP Simplified bold",12),background="white")
###
var_jlp=StringVar()
var_jlp.set("hour")
input_var_jlp=OptionMenu(label_showgraph_tab_1,var_jlp,"hour","date","month","year")
input_var_jlp.grid(row=0,column=0,columnspan=1,padx=3,pady=2,sticky=NW)
input_var_jlp.config(font=("HP Simplified",9),background="white")
button_excute_showgraph_tab_1=Button(label_showgraph_tab_1,text="Show Graph",command=plot)
button_excute_showgraph_tab_1.grid(row=0,column=1,columnspan=1,padx=3,pady=2,sticky=NW)
label_showgraph_tab_1.grid_propagate(False)
button_excute_showgraph_tab_1.config(font=("HP Simplified",9),background="white")

## Tab_2 GUI
###
label_calibration_title=Label(tab_2,text="Calibration Process")
label_calibration_title.grid(row=0,column=0,columnspan=3,padx=3,pady=2,sticky=W)
label_calibration_title.config(font=("HP Simplified bold",12),background="white")
label_jlp_calibration=Label(tab_2,text="JLP Calibration:                                ")
label_jlp_calibration.grid(row=1,column=0,columnspan=1,padx=3,pady=2,sticky=W)
label_jlp_calibration.config(font=("HP Simplified",11),background="white")
input_jlp_calibration=Entry(tab_2,width=16,relief=SOLID)
input_jlp_calibration.grid(row=1,column=1,columnspan=2,padx=3,pady=2,sticky=E)
input_jlp_calibration.config(font=("HP Simplified",10),background="white")
label_weir_calibration=Label(tab_2,text="Weirbox Calibration:           ")
label_weir_calibration.grid(row=2,column=0,columnspan=1,padx=3,pady=2,sticky=W)
label_weir_calibration.config(font=("HP Simplified",11),background="white")
input_weir_calibration=Entry(tab_2,width=16,relief=SOLID)
input_weir_calibration.grid(row=2,column=1,columnspan=2,padx=3,pady=2,sticky=E)
input_weir_calibration.config(font=("HP Simplified",10),background="white")
button_excute_calibration= Button(tab_2,text="Execute",command=processing_jlp_calibration)
button_excute_calibration.grid(row=3,column=2,columnspan=1,padx=3,pady=2,sticky=E)
button_excute_calibration.config(font=("HP Simplified",9),background="white")
###
spacer1 = Label(tab_2, text="",background="white")
spacer1.grid(row=0,column=4)
label_showgraph_tab_2=LabelFrame(tab_2,text="After JLP Calibration",height=640,width=722)
label_showgraph_tab_2.grid(row=0,column=5,rowspan=1000,columnspan=1000,padx=3,pady=2,sticky=NW)
label_showgraph_tab_2.config(font=("HP Simplified bold",12),background="white")
###
var_jlp_calibrated=StringVar()
var_jlp_calibrated.set("hour")
input_var_jlp_calibrated=OptionMenu(label_showgraph_tab_2,var_jlp_calibrated,"hour","date","month","year")
input_var_jlp_calibrated.grid(row=0,column=0,columnspan=1,padx=3,pady=2,sticky=NW)
input_var_jlp_calibrated.config(font=("HP Simplified",9),background="white")
button_excute_showgraph_tab_2=Button(label_showgraph_tab_2,text="Show Graph",command=plot_caliberated)
button_excute_showgraph_tab_2.grid(row=0,column=1,columnspan=1,padx=3,pady=2,sticky=NW)
label_showgraph_tab_2.grid_propagate(False)
button_excute_showgraph_tab_2.config(font=("HP Simplified",9),background="white")

## Save GUI
label_save_title=Label(tab_3,text="Save Calibrated JLP in .xlsx")
label_save_title.grid(row=0 ,column=0,columnspan=3,padx=3,pady=2,sticky=W)
label_save_title.config(font=("HP Simplified bold",12),background="white")
label_save=Label(tab_3,text="File Name:")
label_save.grid(row=1,column=0,columnspan=1,padx=3,pady=2,sticky=W)
label_save.config(font=("HP Simplified",11),background="white")
input_save=Entry(tab_3,width=16,relief=SOLID)
input_save.grid(row=1,column=1,columnspan=2,padx=3,pady=2,sticky=E)
input_save.config(font=("HP Simplified",10),background="white")
button_excute_save = Button(tab_3,text="Execute",command=save_xlsx)
button_excute_save.grid(row=2,column=2,columnspan=1,padx=3,pady=2,sticky=E)
button_excute_save.config(font=("HP Simplified",9),background="white")

#
root.update()
root.update_idletasks()
root.mainloop()