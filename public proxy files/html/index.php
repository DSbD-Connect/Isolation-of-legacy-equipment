<!DOCTYPE html>
<html>
    <head>
        <title>PHP Test</title>
    </head>
    <body>

    <?php
        if (isset($_POST['do_scan'])){
            $fp = fsockopen("udp://xxx.xxx.xxx.xxx", 5533, $errno, $errstr);
            if (!$fp) {
                echo "ERROR: $errno - $errstr<br />\n";
            } else {
                fwrite($fp, "SCAN\n");
                fclose($fp);
            }
        }
    ?>
      
    <div><a href="images">Scanned Images</a></div>
    <p></p>
    <div><form method="post" action=""><input type="submit" value="take scan" name="do_scan"/></form></div>

    </body>
</html>




