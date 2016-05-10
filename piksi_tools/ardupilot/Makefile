spec_file=dataflash2sbpjson.spec
pyinstaller=pyinstaller

ifneq (,$(findstring /cygdrive/,$(PATH)))
    UNAME := Cygwin
    PLAT_ARGS="-F"
else
ifneq (,$(findstring WINDOWS,$(PATH)))
    UNAME := Windows
    PLAT_ARGS="-F"
else
    UNAME := $(shell uname -s)
    PLAT_ARGS="-w"
endif
endif


dataflash2sbpjson: $(spec_file)
	make clean
	pyinstaller --clean --log-level=WARN --paths=/Users/dzollo/source/mavlink --debug $(PLAT_ARGS) $(spec_file) -y
	echo "Pyinstaller completed. Building platform installer."

clean:
	rm -rf build dist


