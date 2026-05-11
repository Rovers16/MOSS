CXX      = g++
CXXFLAGS = -Wall -O2 -pthread -std=c++17
INCLUDES = -Iinclude
SRCDIR   = src
SRCS     = $(wildcard $(SRCDIR)/*.cpp)
TARGET   = moss_sync

.PHONY: all clean demo

all: $(TARGET)

$(TARGET): $(SRCS)
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(SRCS) -o $(TARGET)

demo: all
	./$(TARGET)

clean:
	rm -f $(TARGET)
