# byteorder.py: VISUAL test, needs a human. Fills the LEFT half with pixel bytes F8 00 and the
# RIGHT half with 00 F8 (both are "pure red" in RGB565, in opposite byte orders). Whichever half
# shows RED is the byte order the panel wants on the wire, and therefore the order asset files
# must use. Also writes "TOP" along the top edge and "L" at left so orientation can be checked.
# Leaves the pattern on screen. Rerun safe.
from lcdbench import Bench
b = Bench(baud=62_500_000)
mv = memoryview(b.buf)
for y in range(240):
    row = y * 480
    for x in range(0, 120):
        mv[row + 2*x] = 0xF8; mv[row + 2*x + 1] = 0x00
    for x in range(120, 240):
        mv[row + 2*x] = 0x00; mv[row + 2*x + 1] = 0xF8
b.fb.fill_rect(0, 0, 240, 12, 0xFFFF)
b.fb.text("TOP   left=F800  right=00F8", 4, 2, 0x0000)
b.fb.fill_rect(0, 100, 10, 40, 0xFFFF); b.fb.text("L", 1, 116, 0x0000)
b.show()
print("RESULT byteorder pattern shown; ask: which half is RED, is TOP at the top, is L on the left?")
