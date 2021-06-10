from reportlab.pdfgen.canvas import Canvas
import os

curr_path = os.path.dirname(__file__)

canvas = Canvas("/home/francesco/Scaricati/file.pdf", pagesize=(612.0, 792.0))
canvas.drawImage(curr_path + "/logo.png", 280, 720, 50, 50, [0,0,0,0,0,0])
canvas.drawString(280, 700, "InQueue")

canvas.drawString(250, 650, "IL TUO BIGLIETTO")
canvas.drawString(100,600, "Hai prenotato " + "TAGLIO CAPELLI")
canvas.drawString(100,580, "presso " + "TAGLIO CAPELLI")
canvas.drawString(100,560, "per il " + "TAGLIO CAPELLI" + " alle ore " + "TAGLIO DI CAPELLI")
canvas.drawString(100,580, "presso " + "TAGLIO CAPELLI")
canvas.save()