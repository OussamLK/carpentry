import { useCallback, useEffect, useMemo, useState } from "react";
import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg";
import "./App.css";

const DOMAIN = "/api";

class API {
  domain: string;
  constructor(domain: string) {
    this.domain = domain;
  }
  post = async (route: string, body: any) => {
    const resp = await fetch(this.domain + "/problems", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    return data;
  };

  solution = async (
    problem: Problem,
  ): Promise<{ illustration: string; unfits: Piece[] }> => {
    const solutionData = (await this.post("/problems", problem)) as unknown;
    console.debug(`solution data is: `, solutionData);
    const { illustration, unfits } = solutionData as {
      illustration: string;
      unfits: Piece[];
    };
    return { illustration, unfits };
  };
}

const api = new API(DOMAIN);

type Problem = {
  board: Board;
  sawWidth: number;
  pieces: Piece[];
};
type Piece = {
  id: number;
  height: number;
  width: number;
  canRotate: boolean;
};

type Board = {
  height: number;
  width: number;
};

function App() {
  const [boardHeight, setBoardHeight] = useState("");
  const [boardWidth, setBoardWidth] = useState("");
  const [sawWidth, setSawWidth] = useState("2.5");
  const [pieces, setPieces] = useState<Piece[]>([]);
  const [imageData, setImageData] = useState<string | undefined | "loading">(
    undefined,
  );
  const [unfits, setUnfits] = useState<Piece[]>([]);
  const problem = useMemo<Problem | undefined>(() => {
    const boardWidthF = Number.parseFloat(boardWidth.replace(",", "."));
    const boardHeighF = Number.parseFloat(boardHeight.replace(",", "."));
    const sawWidthF = Number.parseFloat(sawWidth);
    if (Number.isNaN(boardHeighF) || Number.isNaN(boardWidthF))
      return undefined;
    if (pieces.length === 0) return undefined;
    return {
      board: { height: boardHeighF, width: boardWidthF },
      sawWidth: sawWidthF,
      pieces,
    };
  }, [boardHeight, boardWidth, pieces]);
  async function getSolution() {
    if (problem) {
      setImageData("loading");
      console.debug("submitting solution...");
      const { illustration, unfits } = await api.solution(problem);
      setImageData(illustration);
      setUnfits(unfits);
    }
  }

  return (
    <div>
      <form onSubmit={(e) => e.preventDefault()}>
        <div>
          <h2>Planche:</h2>
          <label>
            Hauteur (mm) &nbsp;
            <input
              value={boardHeight}
              onChange={(e) => setBoardHeight(e.currentTarget.value)}
            ></input>
            <br />
          </label>
          <label>
            Largeur (mm): &nbsp;
            <input
              value={boardWidth}
              onChange={(e) => setBoardWidth(e.currentTarget.value)}
            ></input>
          </label>
        </div>
        <div>
          <h2>Scie</h2>
          <label>
            Largeur de la scie: &nbsp;
            <FloatInput
              value={sawWidth}
              onError={(e) => 0}
              onChange={(v) => setSawWidth(v)}
            />
          </label>
        </div>
        <Pieces pieces={pieces} setPieces={setPieces} />
      </form>

      <button onClick={getSolution} disabled={problem === undefined}>
        Résoudre
      </button>
      <br />
      <Unfits unfits={unfits} />
      <br />
      <Image data={imageData} />
      <br />
      <button disabled={imageData === undefined}>Imprimer</button>
    </div>
  );
}

function Unfits({ unfits }: { unfits: Piece[] }) {
  if (unfits.length > 0) {
    return (
      <div>
        <h3>Je n'ai pas pu inclure:</h3>
        <ol>
          {unfits.map((u) => (
            <li key={u.id}>
              Coupe: {u.height}mm x {u.width}mm
            </li>
          ))}
        </ol>
      </div>
    );
  }
}

function Image({ data }: { data: undefined | "loading" | string }) {
  if (data == "loading") {
    return <p>Calcule de solution...</p>;
  } else if (data !== undefined) {
    return <img src={`data:image/png;base64,${data}`} height={"800em"} />;
  }
}

function Pieces({
  pieces,
  setPieces,
}: {
  pieces: Piece[];
  setPieces: (pieces: Piece[]) => void;
}) {
  const [pieceEditorPresets, setPieceEditorPreset] = useState<Piece | undefined >(undefined)
  return (
    <div>
      <h2>Coupes</h2>
      <ul>
        {pieces.map((p) => (
          <Piece key={p.id} piece={p} setPieces={setPieces} setPieceEditorPresets={setPieceEditorPreset} />
        ))}
      </ul>
      <PieceEditor setPieces={setPieces} presets={pieceEditorPresets} />
    </div>
  );
}

function Piece({ piece, setPieces, setPieceEditorPresets }: { piece: Piece; setPieces: any, setPieceEditorPresets:any }) {
  function deletePiece(id: number) {
    setPieces(prev => prev.filter((p) => p.id !== id));
  }
  function editPiece(id: number) {
    setPieces(prev => prev.filter((p) => p.id !== id));
    setPieceEditorPresets(piece)
  }
  function duplicatePiece() {
   setPieces(prev=> [...prev, {...piece, id:prev.length}]) 
  }
  return (
    <li>
      Coupe {piece.id + 1}: {piece.height} mm x {piece.width} mm.{" "}
      {piece.canRotate ? "Peut tourner" : "fixe"}{" "}
      <button className="piece-button" onClick={() => deletePiece(piece.id)}>supprimer</button>
      <button className="piece-button" onClick={() => editPiece(piece.id)}>modifier</button>
      <button className="piece-button" onClick={() => duplicatePiece(piece.id)}>dupliquer</button>
    </li>
  );
}

function PieceEditor({ setPieces, presets }: { setPieces: any, presets:any }) {
  const [height, setHeight] = useState('');
  const [width, setWidth] = useState('');
  const [canRotate, setCanRotate] = useState(false);
  const [validPiece, setValidPiece] = useState(false);
  useEffect(()=>{
    if (presets){
      setHeight(String(presets.height))
      setWidth(String(presets.width))
      setCanRotate(presets.canRotate)
      setValidPiece(true)
    }
  }, [presets])

  function validate(height: string, width: string) {
    const heightF = Number.parseFloat(height);
    const widthF = Number.parseFloat(width);
    if (Number.isNaN(heightF) || Number.isNaN(widthF)) {
      setValidPiece(false);
    } else setValidPiece(true);
  }

  function onAdd() {
    const heightF = Number.parseFloat(height.replace(",", "."));
    const widthF = Number.parseFloat(width.replace(",", "."));
    //@ts-ignore
    setPieces((prev) => [
      ...prev,
      { id: prev.length, height: heightF, width: widthF, canRotate },
    ]);
    setHeight("");
    setWidth("");
    setCanRotate(false);
    setValidPiece(false);
  }

  return (
    <div className="piece-editor">
      <label>
        Hauteur (mm): &nbsp;{" "}
        <FloatInput
          value={height}
          onChange={(v) => {
            setHeight(v);
            validate(v, width);
          }}
          onError={() => 0}
        />
      </label>
      <br />
      <label>
        Largeur (mm): &nbsp;{" "}
        <FloatInput
          value={width}
          onChange={(v) => {
            setWidth(v);
            validate(height, v);
          }}
          onError={() => 0}
        />
      </label>{" "}
      <br />
      <label>
        Peut tourner:{" "}
        <input
          checked={canRotate}
          onChange={(e) => setCanRotate((prev) => !prev)}
          type="checkbox"
        ></input>
      </label>
      <br />
      <button disabled={!validPiece} onClick={onAdd}>
        Ajouter Coupe
      </button>
    </div>
  );
}

function FloatInput({
  value,
  onChange,
  onError,
}: {
  value: string;
  onChange: (v: string) => void;
  onError: (error: boolean) => void;
}) {
  const [error, setError] = useState(false);
  function onInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const new_input = e.currentTarget.value;
    const fixed_comma = new_input.replace(",", ".");
    const n = Number.parseFloat(fixed_comma);
    if (Number.isNaN(n)) {
      setError(true);
      onError(true);
    } else {
      setError(false);
      onError(false);
    }
    onChange(new_input);
  }

  return (
    <input
      value={value}
      onChange={onInputChange}
      className={error ? "float-input-error" : "float-input"}
    ></input>
  );
}

export default App;
