<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>T9AMAP</title>
<style>
body {
  background-color: #ffcc00;
  text-align: center;
  font-family: sans-serif;
  padding: 10px;
}
select, input[type=text], input[type=tel] {
  background-color: #ffffff;
  border: 2px solid #333333;
  box-sizing: border-box;
  margin-bottom: 2px;
}
select, input[type=text] {
  width: 100%;
}
input[type=tel] {
  width: 5em;
}
select:focus, input:focus {
  background-color: #99ccff;
  outline: 3px solid #000000;
}
</style>
</head>
<body>
<form action="/query" method="POST">

<b>START</b><br>
<select name="start_sel">
  <option value="">-</option>
% for f in favs:
  <option value="{{f}}">{{f}}</option>
% end
</select><br>
<input type="text" name="start_txt"><br>

<b>DEST</b><br>
<select name="dest_sel">
  <option value="">-</option>
% for f in favs:
  <option value="{{f}}">{{f}}</option>
% end
</select><br>
<input type="text" name="dest_txt"><br>

<b>TIME</b><br>
<input type="tel" name="time" maxlength="4" placeholder="HHMM" size="4">
<label><input type="radio" name="type" value="ARR" checked>ARR</label>
<label><input type="radio" name="type" value="DEP">DEP</label><br><br>

<input type="submit" value="Submit">
</form>
<p><a href="/admin">admin</a></p>
</body>
</html>
