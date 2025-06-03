# WaveNet

## Preparación

Ejecutar `$ make` y después `$ cd WaveNetAplicacion/wavenetaplicacion`.

## Ejecución

### Activar mesh hub

```
$ python3 main_meshhub.py --verbose --localp 9000
```

### Activar file hub

```
$ python3 FileHub.py --verbose --localp 9001 --localc 0,9000 -n 1
```

### Activar file DAEMON

```
$ python3 FileServiceDaemon.py --verbose --localp 9002 --localc 1,9001 -n 2 --hub-id 1 --dir ./carpeta_compartida
```

### Activar sercivio IRC

```
$ python3 irc_bot.py --hub-id 1 --server 127.0.0.1 --port 6667 --channel "#wavenet"   --nick "WaveBot" --out-dir ./descargas --localp 9005 --localc 2,9002 -n 3
```

### Consulta por archivo

```
$ python3 FileClient.py --verbose --localp 9003 -n 4 --localc 0,9000 --hub-id 1 --out-dir ./descargas -f unga_bunga.md
```

### Conexión IRC

```
$ irssi -n jesusg -c 127.0.0.1 -p 6667
> /join #wavenet
> !list
> !get prueba.txt
```
