"""
いちいちlibpafe.って書くのめんどいからライブラリっぽくした
"""

from __future__ import print_function
from ctypes import *

libpafe = cdll.LoadLibrary("/usr/local/lib/libpafe.so")

###関数の引数,返り値の指定
libpafe.pasori_open_port.argtypes = (c_char_p,) #文字列引数の指定
libpafe.pasori_open_port.restype = c_void_p
libpafe.pasori_init.argtypes=(c_void_p,) #引数の指定
libpafe.felica_polling.argtypes = (c_void_p,c_int,c_int,c_int) #引数の指定
libpafe.felica_polling.restype = c_void_p
libpafe.felica_get_idm.argtypes = (c_void_p,c_void_p) #引数の指定
libpafe.felica_get_idm.restype = c_void_p
libpafe.free.argtypes=(c_void_p,) #引数の指定
libpafe.pasori_close.argtypes=(c_void_p,) #引数の指定
libpafe.pasori_set_timeout.argtypes=(c_void_p,c_int)    
###


def pasori_open_port(port_name:str):
    """
    :param port_name .encodeでバイト形式に変換した文字列
    """
    return libpafe.pasori_open_port(port_name)

def pasori_init(pasori):
    return libpafe.pasori_init(pasori)

def pasori_close(pasori):
    return libpafe.pasori_close(pasori)

def pasori_set_timeout(pasori,timeout:int):
    """
    timeout以上受信しなければ次にうつる
    :param timeout: [ms]
    """
    return libpafe.pasori_set_timeout(pasori,timeout)

def felica_polling(pasori,FELICA_POLLING_ANY=0xffff):
    return libpafe.felica_polling(pasori, FELICA_POLLING_ANY,0,0)

def felica_get_id(felica):
    idm=c_uint64()
    libpafe.felica_get_idm(felica, byref(idm))
    return idm

def free(felica):
    return libpafe.free(felica)