from solver import Board, Piece, solver, pywraplp
import logging
logging.basicConfig(level=logging.DEBUG)

board = Board(height=1850*10, width=468*10, saw_width=int(2.5*10))
# 2 x tiroir 536, 182
# 2x etageres 420, 500
pieces_str = '''536,182 536,182 500,420'''
pieces = Piece.parse_pieces(pieces_str, board)
LP = len(pieces)
fillers = [Piece(len(pieces)+1, 809*10, 468*10, board)]
# fillers.append(Piece(LP, 6800, 5000, board))

for i, piece in enumerate(pieces[:-1]):
    for other in pieces[i+1:]:
        piece.creat_non_overlapping_constraint(other)


extra = [filler.filler_constraint(pieces+fillers[i+1:])
         for i, filler in enumerate(fillers)]
if __name__ == '__main__':
    logging.info("starting the solver...")
    solver.Maximize(solver.Sum(extra))
    status = solver.Solve()
    print(f"The number of constraints are {len(solver.constraints())}")
    if status == pywraplp.Solver.OPTIMAL:
        print(f"could fit in {sum(ex.solution_value()
              for ex in extra)} extras")
        for piece in pieces:
            print(f"Piece {piece.id} is set in ( {
                piece.lx.solution_value()} , {piece.ly.solution_value()} )")
        for i, filler in enumerate(fillers):
            if extra[i].solution_value() > 0:
                print(f"Filler {filler.id} is at position ( {
                    filler.lx.solution_value()} , {filler.ly.solution_value()} )")
        from illustrate import BoardIllustrator
        illustrator = BoardIllustrator(board.height, board.width)
        for piece in pieces:
            illustrator.add_rectangle(piece.lx.solution_value(),
                                      piece.ly.solution_value(), piece.height, piece.width, '#463C3D', annotate=True, text_color='white')
        for i, filler in enumerate(fillers):
            if extra[i].solution_value() > 0:
                filler = fillers[i]
                illustrator.add_rectangle(filler.lx.solution_value(
                ), filler.ly.solution_value(), filler.height, filler.width, '#6bfa94', annotate=True)
        illustrator.show()
    else:
        print("I couldnt find a solution")
