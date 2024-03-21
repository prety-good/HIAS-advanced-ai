import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from main import AIPlayer, RandomPlayer, HumanPlayer
from func_timeout import func_timeout, FunctionTimedOut
from game import Game
import datetime
import time
from copy import deepcopy

class ChessBoard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('棋盘界面')
        self.setGeometry(100, 100, 900, 600)
        self.cell_size = 75  # 每个格子的大小
        self.board_state = [['.'] * 8 for _ in range(8)]  # 记录每个格子的状态，None表示空白，'X'表示黑棋，'O'表示白棋
        self.board_state[3][4], self.board_state[4][3] = 'X', 'X'  # 黑棋棋子
        self.board_state[3][3], self.board_state[4][4] = 'O', 'O'  # 白棋棋子

    def paintEvent(self, event):
        painter = QPainter(self)
        # 绘制棋盘网格
        self.draw_chessboard(painter)
        # 绘制棋子
        self.draw_pieces(painter)

    def draw_chessboard(self, painter):
        # 设置棋盘的尺寸和行列数
        board_size = 600
        rows = cols = 8
        cell_size = self.cell_size

        # 绘制棋盘网格
        for row in range(rows):
            for col in range(cols):
                # 计算每个格子的左上角坐标
                x = col * cell_size
                y = row * cell_size
                # 根据奇偶行列交替绘制黑白格子
                if (row + col) % 2 == 0:
                    painter.fillRect(x, y, cell_size, cell_size, QColor(255, 206, 158))  # 白色格子
                else:
                    painter.fillRect(x, y, cell_size, cell_size, QColor(209, 139, 71))  # 黑色格子

        # 绘制棋盘边框
        painter.setPen(Qt.black)
        painter.drawRect(0, 0, board_size, board_size)

    def draw_pieces(self, painter):
        for row in range(8):
            for col in range(8):
                if self.board_state[row][col] == 'X':
                    self.draw_piece(painter, row, col, Qt.black)
                elif self.board_state[row][col] == 'O':
                    self.draw_piece(painter, row, col, Qt.white)

    def draw_piece(self, painter, row, col, color):
        # 计算围棋子的中心位置
        stone_size = self.cell_size // 2
        x = col * self.cell_size + self.cell_size // 2 - stone_size // 2
        y = row * self.cell_size + self.cell_size // 2 - stone_size // 2
        # 绘制围棋子
        painter.setBrush(color)
        painter.drawEllipse(x, y, stone_size, stone_size)

    def refresh_board(self, board_array):
        self.board_state = board_array
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 获取点击位置的坐标
            x = event.x()
            y = event.y()
            # 计算点击位置所在的行列
            row = y // self.cell_size
            col = x // self.cell_size
            print("左键点击位置：行", row, "列", col)
            # 更新格子状态并重绘
            # self.board_state[row][col] = 'X'  # 这里默认为黑棋，你可以根据需要修改
            # self.refresh_board(self.board_state)
            return (row, col)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('黑白棋对弈')
        self.setGeometry(100, 100, 900, 600)

        # 创建棋盘界面
        self.chessboard = ChessBoard()
        self.chessboard.setGeometry(0, 0, 600, 600)
        self.chessboard.setParent(self)

        # 添加开始按钮
        self.start_button = QPushButton('开始', self)
        self.start_button.setGeometry(700, 50, 150, 50)
        self.start_button.clicked.connect(self.begin)

    def begin(self):
        self.game_thread = GameThread()
        self.game_thread.update_signal.connect(self.chessboard.refresh_board)
        self.game_thread.start()
        

class GameThread(QThread):
    update_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        # 人类玩家黑棋初始化
        black_player = HumanPlayer("X")
        # AI 玩家 白棋初始化
        white_player = AIPlayer("O")
        # 游戏初始化，第一个玩家是黑棋，第二个玩家是白棋
        self.game = Game(black_player, white_player)

    def run(self):    
        # 在这里执行游戏循环的代码
        # 开始下棋
        # 定义统计双方下棋时间
        total_time = {"X": 0, "O": 0}
        # 定义双方每一步下棋时间
        step_time = {"X": 0, "O": 0}
        # 初始化胜负结果和棋子差
        winner = None
        diff = -1
        # 游戏开始        print('\n=====开始游戏!=====\n')
        # 棋盘初始化
        self.game.board.display(step_time, total_time)
        while True:
            # 切换当前玩家,如果当前玩家是 None 或者白棋 white_player，则返回黑棋 black_player;
            #  否则返回 white_player。
            self.game.current_player = self.game.switch_player(self.game.black_player, self.game.white_player)
            start_time = datetime.datetime.now()
            # 当前玩家对棋盘进行思考后，得到落子位置
            # 判断当前下棋方
            color = "X" if self.game.current_player == self.game.black_player else "O"
            # 获取当前下棋方合法落子位置
            legal_actions = list(self.game.board.get_legal_actions(color))
            # print("%s合法落子坐标列表："%color,legal_actions)
            if len(legal_actions) == 0:
                # 判断游戏是否结束
                if self.game.game_over():
                    # 游戏结束，双方都没有合法位置
                    winner, diff = self.game.board.get_winner()  # 得到赢家 0,1,2
                    break
                else:
                    # 另一方有合法位置,切换下棋方
                    continue

            board = deepcopy(self.game.board._board)

            # legal_actions 不等于 0 则表示当前下棋方有合法落子位置
            try:
                for i in range(0, 3):
                    if isinstance(self.game.current_player, HumanPlayer):
                        action = self.chessboard.mousePressEvent()
                    else:
                        # 获取落子位置
                        action = func_timeout(60, self.game.current_player.get_move,
                                          kwargs={'board': self.game.board})

                    # 如果 action 是 Q 则说明人类想结束比赛
                    if action == "Q":
                        # 说明人类想结束游戏，即根据棋子个数定输赢。
                        break
                    if action not in legal_actions:
                        # 判断当前下棋方落子是否符合合法落子,如果不合法,则需要对方重新输入
                        print("你落子不符合规则,请重新落子！")
                        continue
                    else:
                        # 落子合法则直接 break
                        break
                else:
                    # 落子3次不合法，结束游戏！
                    winner, diff = self.game.force_loss(is_legal=True)
                    break
            except FunctionTimedOut:
                # 落子超时，结束游戏
                winner, diff = self.game.force_loss(is_timeout=True)
                break

            # 结束时间
            end_time = datetime.datetime.now()
            if board != self.game.board._board:
                # 修改棋盘，结束游戏！
                winner, diff = self.game.force_loss(is_board=True)
                break
            if action == "Q":
                # 说明人类想结束游戏，即根据棋子个数定输赢。
                winner, diff = self.game.board.get_winner()  # 得到赢家 0,1,2
                break

            if action is None:
                continue
            else:
                # 统计一步所用的时间
                es_time = (end_time - start_time).seconds
                if es_time > 60:
                    # 该步超过60秒则结束比赛。
                    print('\n{} 思考超过 60s'.format(self.game.current_player))
                    winner, diff = self.game.force_loss(is_timeout=True)
                    break

                # 当前玩家颜色，更新棋局
                self.game.board._move(action, color)

                # 统计每种棋子下棋所用总时间
                if self.game.current_player == self.game.black_player:
                    # 当前选手是黑棋一方
                    step_time["X"] = es_time
                    total_time["X"] += es_time
                else:
                    step_time["O"] = es_time
                    total_time["O"] += es_time
                # 显示当前棋盘
                self.game.board.display(step_time, total_time)
                # 刷新棋盘
                self.update_signal.emit(self.game.board._board)
                # 判断游戏是否结束
                if self.game.game_over():
                    # 游戏结束
                    winner, diff = self.game.board.get_winner()  # 得到赢家 0,1,2
                    break

        print('\n=====游戏结束!=====\n')
        self.game.board.display(step_time, total_time)
        self.game.print_winner(winner)

        # 返回'black_win','white_win','draw',棋子数差
        if winner is not None and diff > -1:
            result = {0: 'black_win', 1: 'white_win', 2: 'draw'}[winner]


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())
    
    # 人类玩家黑棋初始化
    black_player = RandomPlayer("X")

    # AI 玩家 白棋初始化
    white_player = AIPlayer("O")

    # AI 玩家 白棋初始化
    # white_player = HumanPlayer("O")

    # 游戏初始化，第一个玩家是黑棋，第二个玩家是白棋
    game = Game(black_player, white_player)

    # 开始下棋
    game.run()



