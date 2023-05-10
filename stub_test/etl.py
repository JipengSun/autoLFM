from opto import Opto

o = Opto(port='COM4')
o.connect()
o.current(50.0)
o.close(soft_close=True)