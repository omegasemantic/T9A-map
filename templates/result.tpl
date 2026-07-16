<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>T9AMAP — result</title>
</head>
<body>
<p>{{origin}} &gt; {{dest}}</p>
<p>Arrive: {{arrival or 'unknown'}}</p>

%for step in steps:
  %if step['type'] == 'WALK':
<p>WALK: {{step['instruction']}} ({{step['distance']}})</p>
  %else:
<p>
{{step['dep_time']}} {{step['type']}} {{step['line']}} towards {{step['headsign']}}. Depart {{step['depart']}}<br>
{{step['arr_time']}} arrive {{step['arrive']}}. {{step['stops']}} stops
</p>
  %end
%end

<p>Duration: {{duration}} ({{distance}})</p>
<p><a href="/">[new query]</a></p>
</body>
</html>
