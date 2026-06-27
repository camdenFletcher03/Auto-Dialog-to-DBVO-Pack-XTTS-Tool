unit ExportPlayerDialogue;

var
  slExport: TStringList;

function CleanCSV(s: string): string;
begin
  Result := StringReplace(s, '"', '""', [rfReplaceAll]);
  Result := '"' + Result + '"';
end;

function GetHexFormID(e: IInterface): string;
begin
  Result := IntToHex(GetLoadOrderFormID(e), 8);
end;

// Validation identify "real" spoken lines
function IsValidPlayerLine(val: string): boolean;
begin
  Result := (not SameText('', val)) 
    and (not SameText('...', val)) 
    and ((Pos(')', val) = Length(val)) or (Pos(')', val) = 0)) 
    and (Pos(#8216, val) = 0) 
    and (Pos('-', val) <> 1) 
    and (Pos(#8217, val) = 0) 
    and (Pos(#8220, val) = 0) 
    and (Pos(#8221, val) = 0) 
    and (Pos(#8212, val) = 0) 
    and (Pos(#8211, val) = 0) 
    and (Pos(#8230, val) = 0) 
    and (Pos('*', val) = 0) 
    and (Pos('...', val) <> 1) 
    and (Pos(';', val) = 0) 
    and (Pos('[', val) = 0) 
    and ((Pos('<', val) = 0) or ((Pos('<', val) > Pos('(', val)) and (Pos('(', val) > 1))) 
    and (not (Pos('(', val) = 1));
end;

function Initialize: Integer;
begin
  slExport := TStringList.Create;
  slExport.Add('RecordType,FormID,Plugin,EDID,Text');
  Result := 0;
end;

function Process(e: IInterface): Integer;
var
  recType, fid, plugin, edid, rawText, snam: string;
  fullElement: IInterface;
begin
  recType := Signature(e);
  if recType <> 'DIAL' then Exit;

  // Filter by Dialogue Subtype to target standard player choices
  snam := GetElementEditValues(e, 'SNAM');
  if not (SameText('Custom', snam) or SameText('Rumors', snam) or SameText('', snam)) then Exit;

  // Navigate to the FULL subrecord
  fullElement := ElementByPath(e, 'FULL');
  if Assigned(fullElement) then begin
    // Pull the raw string data
    rawText := Trim(VarToStr(GetNativeValue(fullElement)));
    
    // FILTER: Drop the record if it doesn't meet the "real" player voice line criteria
    if not IsValidPlayerLine(rawText) then Exit;
    
    fid := GetHexFormID(e);
    plugin := GetFileName(GetFile(e));
    edid := CleanCSV(EditorID(e));
    
    slExport.Add(Format('%s,%s,%s,%s,%s', [recType, fid, plugin, edid, CleanCSV(rawText)]));
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
      sd.Title := 'Save Filtered Player DIAL Export';
      sd.Filter := 'CSV files (*.csv)|*.csv';
      sd.FileName := 'Filtered_Player_Dialog.csv';
      if sd.Execute then slExport.SaveToFile(sd.FileName);
    finally
      sd.Free;
    end;
  end;
  slExport.Free;
  Result := 0;
end;

end.
