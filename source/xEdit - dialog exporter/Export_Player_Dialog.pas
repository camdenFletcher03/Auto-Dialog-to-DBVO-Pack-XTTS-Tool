unit ExportPlayerDialogAndInfo;

var
  slExport: TStringList;
  slSeen: TStringList;
  currentDialPrompt: string;
  isCurrentDialDuplicate: Boolean;

function CleanCSV(s: string): string;
begin
  // Escape quotes and wrap in quotes to keep the CSV clean
  Result := StringReplace(s, '"', '""', [rfReplaceAll]);
  Result := '"' + Result + '"';
end;

// Strips out game tags like (Persuade), [Attack], (Bribe) etc.
function CleanGameTags(s: string): string;
var
  pStart, pEnd: Integer;
begin
  Result := s;
  
  // Remove (...) tags
  while True do begin
    pStart := Pos('(', Result);
    pEnd := Pos(')', Result);
    if (pStart > 0) and (pEnd > pStart) then
      Delete(Result, pStart, (pEnd - pStart) + 1)
    else
      Break;
  end;

  // Remove [...] tags
  while True do begin
    pStart := Pos('[', Result);
    pEnd := Pos(']', Result);
    if (pStart > 0) and (pEnd > pStart) then
      Delete(Result, pStart, (pEnd - pStart) + 1)
    else
      Break;
  end;

  Result := Trim(Result);
end;

function GetHexFormID(e: IInterface): string;
begin
  Result := IntToHex(GetLoadOrderFormID(e), 8);
end;

function Initialize: Integer;
begin
  slExport := TStringList.Create;
  slSeen := TStringList.Create;
  slSeen.Sorted := True; // Improves lookups dramatically for master file processing
  slSeen.Duplicates := dupIgnore;

  // Standard header schema
  slExport.Add('RecordType,FormID,Plugin,EDID,Text,RNAM - Prompt');
  currentDialPrompt := '';
  isCurrentDialDuplicate := False;
  Result := 0;
end;

function Process(e: IInterface): Integer;
var
  recType, fid, plugin, edid, dialPrompt, infoText, snam: string;
begin
  recType := Signature(e);
  
  // --- CASE 1: WE HIT A DIAL RECORD (The player selection prompt) ---
  if recType = 'DIAL' then begin
    isCurrentDialDuplicate := False;

    // Filter out scene dialogues or combat grunts if needed
    snam := GetElementEditValues(e, 'SNAM');
    if not (SameText('Custom', snam) or SameText('Rumors', snam) or SameText('', snam)) then begin
      currentDialPrompt := ''; 
      Exit;
    end;

    dialPrompt := GetElementEditValues(e, 'RNAM');
    if SameText('', dialPrompt) then
      dialPrompt := GetElementEditValues(e, 'FULL');

    dialPrompt := Trim(dialPrompt);
    if SameText('', dialPrompt) then begin
      currentDialPrompt := '';
      Exit; 
    end;

    // Clean tags like (Persuade) or [Attack] before evaluation
    dialPrompt := CleanGameTags(dialPrompt);
    if SameText('', dialPrompt) then begin
      currentDialPrompt := '';
      Exit;
    end;

    // Skip tracking if we have already exported this text prompt in a prior master file loop
    if slSeen.IndexOf(dialPrompt) <> -1 then begin
      isCurrentDialDuplicate := True;
      currentDialPrompt := '';
      Exit;
    end;

    // Register this prompt so it cannot be duplicated
    slSeen.Add(dialPrompt);

    currentDialPrompt := dialPrompt; 
    fid := GetHexFormID(e);
    plugin := GetFileName(GetFile(e));
    edid := EditorID(e);

    // Export the DIAL row
    slExport.Add(Format('DIAL,%s,%s,%s,%s,%s', [
      fid, 
      plugin, 
      CleanCSV(edid), 
      CleanCSV(dialPrompt), 
      CleanCSV(dialPrompt)
    ]));
  end
  
  // --- CASE 2: WE HIT AN INFO RECORD (The actual voiced response text) ---
  else if recType = 'INFO' then begin
    // If the parent DIAL was dropped as a duplicate, skip its trailing child records too
    if isCurrentDialDuplicate then Exit;

    if currentDialPrompt <> '' then begin
      infoText := Trim(GetElementEditValues(e, 'NAM1 - Response Text'));
      if SameText('', infoText) then
        infoText := Trim(GetElementEditValues(e, 'Text')); // Fallback

      infoText := CleanGameTags(infoText);

      fid := GetHexFormID(e);
      plugin := GetFileName(GetFile(e));
      edid := EditorID(e);

      // Export the child INFO row
      slExport.Add(Format('INFO,%s,%s,%s,%s,', [
        fid,
        plugin,
        CleanCSV(edid),
        CleanCSV(infoText)
      ]));
    end;
  end;

  Result := 0;
end;

function Finalize: Integer;
var
  sd: TSaveDialog;
begin
  if slExport.Count > 1 then begin
    sd := TSaveDialog.Create(nil);
    try
      sd.Title := 'Save Cleaned Player DIAL/INFO Export';
      sd.Filter := 'CSV files (*.csv)|*.csv';
      sd.FileName := 'Player_Dialog.csv';
      if sd.Execute then slExport.SaveToFile(sd.FileName);
    finally
      sd.Free;
    end;
  end;
  slExport.Free;
  slSeen.Free;
  Result := 0;
end;

end.
