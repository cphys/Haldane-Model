ClearAll["Global`*"]

(* Plotting Options
    - finalPlot  -> False: reduces the resolution of the output plot in order to decrease computation time
    -exportGif -> True: exports animated gif file to  directory containing this notebook file
    -showAnimation -> True: displays an animated plot within the notebook *)

finalPlot = True;
exportGif = True;
showAnimation = False;
muResolution = 51;
kResolution = 101;
width = 30;
bound = "infinite";
tVal = "1.00";
t2Val = "0.00";

(* Filenames of Import and Export Data *)

folderName = "muRes" <> ToString[muResolution] <> "_kRes" <> ToString[kResolution] <> "_width" <> ToString[width] <> "_boundary" <> ToString[bound] <> "_t" <> ToString[tVal] <> "_t2" <> ToString[t2Val];
exportFolder = NotebookDirectory[] <> "data/" <> folderName;
fileName1 = exportFolder <> "/berry/";
exportFileName = exportFolder <> "/berryPhase.gif";

(* Adjustable Plot Parameters
    - drange_max/drange_min-> give the min and max range of the imported data
    - plotRangeScales-> % that the plot range should be larger than the maximum data range in the (x,y,z) directions respectively
    -iSize -> image size
    -frameTix -> frame ticks in the x, y, z directions respectively *)

dRangeXmax = \[Pi];
dRangeYmax = \[Pi];
dRangeXmin = -dRangeXmax;
dRangeYmin = -dRangeYmax;
plotRangeScales = {0.1, 0.1, -0.05};
axisLabels = {"\!\(\*SubscriptBox[\(k\), \(x\)]\)","\!\(\*SubscriptBox[\(k\), \(z\)]\)", "E"};
iSize = 400;
fontWeight = Normal;
fontColor = Black;
fontFamily = "Latex";
frameTix = {{-\[Pi], 0, \[Pi]}, {-\[Pi], 0, \[Pi]}, Automatic};
plotStyle = {{Yellow, Opacity[.85]}, {Blue, Opacity[.85]}};
viewPoint = {1.3, -.75, 0};
boxRatios = {1, 1, 1.25};

(* adjusts resolution of final plots based on Plotting Options *)
If[finalPlot,
  {meshPoints = 35,
   perfGoal = "Quality"},
  {meshPoints = 10,
   perfGoal = "Speed"},
  {meshPoints = 10,
   perfGoal = "Speed"}];

(* adjusts data range and plot ranges based on Adjustable Plot Parameters *)
dataRange = {
   {dRangeXmin, dRangeXmax},
   {dRangeYmin, dRangeYmax}};

pRangeFunction[pScale_, minMaxTup_] := pRangeFunction[pScale, minMaxTup] =
  Table[
   minMaxTup[[i]] + pScale*minMaxTup[[i]],
   {i, Length[minMaxTup]}]

plotRange[zValues_] := Append[
  Table[pRangeFunction[plotRangeScales[[i]], dataRange[[i]]], {i, 1, Length[dataRange]}],
  pRangeFunction[plotRangeScales[[3]], MinMax[zValues]]]

(* adjusts plot labels based on Adjustable Plot Parameters *)
fontSize = iSize/16;
textStyle = {FontFamily -> fontFamily, FontWeight -> fontWeight, FontSize -> fontSize, FontColor -> fontColor};
axisLabStyle = Table[Style[axisLabels[[i]], textStyle], {i, Length[axisLabels]}];

(* Imports a list of files within Filenames of Import Data and sorts the list based on the numerical value within the filename. *)
listOfFiles[fileName_] :=
 listOfFiles[fileName] =
  Sort[FileNames["*", fileName]]

sortedList[fileName_] :=
 sortedList[fileName] =
  listOfFiles[fileName][[Ordering@ PadRight@ StringSplit[listOfFiles[fileName],x : NumberString :> ToExpression@x]]]

(*Imports data from sorted list of filenames and organizes into an array of matrices.
    - Matrices are arranged in order based on the numerical values within the filenames.*)
data[fileName_] :=
  data[fileName] =
   Reverse[Table[
     ToExpression[
      Import[sortedList[fileName][[i]], "Table"]],
     {i, 1, Length[sortedList[fileName]]}]];

(* Creates an array of Plots which shows the positive and negative eigenvalues of the Imported data
    - Plots are arranged in order based on the numerical values within the filenames. *)
PlotDensity[posNeg_, imu_] := ListDensityPlot[{data[fileName1][[imu]]},
   DataRange -> dataRange,
   PlotRange -> {{-\[Pi] - .05*\[Pi], \[Pi] + .05*\[Pi]}, {-\[Pi], \[Pi]}, {posNeg*.01, posNeg*.5}},
   ColorFunction -> "Rainbow",
   ColorFunctionScaling -> True,
   BoxRatios -> boxRatios,
   PlotTheme -> "Scientific",
   PlotLegends -> None,
   FrameLabel -> {axisLabStyle[[1]], axisLabStyle[[2]]},
   FrameTicks -> {{{-\[Pi], -\[Pi]/2, 0, \[Pi]/2, \[Pi]}, None}, {{-\[Pi], -\[Pi]/2, 0, \[Pi]/2, \[Pi]}, None}},
   FrameTicksStyle -> Directive[fontColor, fontSize],
   ImageSize -> iSize,
   PerformanceGoal -> "Quality"];

(* Exports animated gif or creates animation within notebook based on selections within Plotting Options. *)
If[exportGif, Export[exportFileName, tableOfPlots]];
If[showAnimation, ListAnimate[tableOfPlots]]
