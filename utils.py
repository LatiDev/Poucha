#STD
import typing

HeaderCellType = typing.TypeVar('HeaderCellType')
ContentCellType = typing.TypeVar('ContentCellType')

class DynamicGrid(typing.Generic[ContentCellType, HeaderCellType]):
    """
    > A DynanmicGrid is a grid with a horizontal and a vertical header.
    > You can freely add any item with horizontal and vertical, it will automaticaly fill the remaining space. 
    > The grid can be of any space horizontaly and verticaly.
    """
    def __init__(self):
        self._content: list[list[list[ContentCellType]]] = [[None]]
        self._horizontal_header: list[HeaderCellType] = [None]
        self._vertical_header: list[HeaderCellType] = []

    def add_value(self, 
        value: ContentCellType, 
        horinzontal: typing.Callable[[ContentCellType], HeaderCellType], 
        vertical: typing.Callable[[ContentCellType], HeaderCellType]
    ):
        if not horinzontal in self._horizontal_header:
            self._horizontal_header.append(horinzontal)
            self._content[0].append(horinzontal)

        if not vertical in self._vertical_header:
            self._vertical_header.append(vertical)
            self._content.append([vertical])

        h_index: int = self._horizontal_header.index(horinzontal)
        v_index: int = self._vertical_header.index(vertical) + 1

        i = 0
        while i < len(self._horizontal_header) - len(self._content[v_index]):
            self._content[v_index].append([])

        self._content[v_index][h_index].append(value)
        
        for ri in range(1, len(self._vertical_header) + 1):
            i = 0
            while i < len(self._horizontal_header) - len(self._content[ri]):
                self._content[ri].append([])

    def get_at(self, rindex: int, cindex: int):
        return self._content[rindex][cindex]
    
    @property
    def raw(self):
        return self._content

    @property
    def horizontal(self):
        return self._horizontal_header[1:]
    
    @property
    def width(self):
        return len(self._horizontal_header)

    @property
    def vertical(self):
        return self._vertical_header

    @property
    def height(self):
        return len(self._vertical_header) + 1

    @property
    def topleft(self):
        return self._content[0][0]

    @topleft.setter
    def topleft(self, value):
        self._content[0][0] = value
        self._horizontal_header[0] = value

    @property
    def biggest_cell(self):
        mlvalue, mrvalue, max_ = None, None, 0
        for ri in range(1, len(self._vertical_header)):
            for ci in range(1, len(self._horizontal_header)):
                count: int = len(self._content[ri][ci])
                if max_ < count:
                    mlvalue = self._vertical_header[ri]
                    mrvalue = self._horizontal_header[ci]
                    max_ = count
        return mlvalue, mrvalue, max_
    
    def iter(self):
        for vindex in range(len(self.vertical)):
            for hindex in range(len(self.horizontal)):
                yield vindex, hindex, self.get_at(vindex + 1, hindex + 1)

    def convert_content(self, 
        conv_cell: typing.Callable[[ContentCellType]],
        conv_header: typing.Callable[[HeaderCellType]]
    ):
        output = [[[] for _ in range(len(self._horizontal_header))] for _ in range(len(self._vertical_header) + 1)]

        for ci in range(1, len(self._horizontal_header)):
            for ri in range(1, len(self._vertical_header) + 1):
                output[ri][ci] = conv_cell(self._content[ri][ci])

        for ci in range(1, len(self._horizontal_header)):
            output[0][ci] = conv_header(self._horizontal_header[ci])

        for ri in range(len(self._vertical_header)):
            output[ri + 1][0] = conv_header(self._vertical_header[ri])

        output[0][0] = None

        return output

    def hiter(self, vvalue: HeaderCellType):
        index: int = self._vertical_header.index(vvalue)

        for vindex in range(len(self.vertical) + 1):
            yield self._content[index + 1][vindex + 1]

    def __str__(self):
        for vindex in range(len(self.vertical)):
            print(self._content[vindex]) 