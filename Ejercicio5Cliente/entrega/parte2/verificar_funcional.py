import json, urllib.request, urllib.parse, urllib.error, uuid, pathlib, http.client, re, sys
ROOT=pathlib.Path(__file__).resolve().parent
results=[]
tag='QA_'+uuid.uuid4().hex[:10]
def request(path, data=None, method=None, port=8082, form=False):
    body=urllib.parse.urlencode(data).encode() if form else (json.dumps(data).encode() if data is not None else None)
    r=urllib.request.Request(f'http://localhost:{port}{path}',data=body,method=method or ('POST' if data is not None else 'GET'),headers={'Content-Type':'application/x-www-form-urlencoded' if form else 'application/json'})
    try:
        with urllib.request.urlopen(r,timeout=20) as response:
            text=response.read().decode(); status=response.status
            try: value=json.loads(text)
            except ValueError: value=text
            return status,value
    except urllib.error.HTTPError as e: return e.code,e.read().decode()
    except http.client.IncompleteRead: return 599, "Respuesta HTML incompleta"
def check(name, condition):
    results.append({'prueba':name,'resultado':'OK' if condition else 'FALLO'})
    print(results[-1],flush=True)
def api(path,data=None,method=None):
    status,value=request(path,data,method,8081)
    if status!=200: raise RuntimeError(f'{path}: HTTP {status}')
    return value
def find(path, field, value): return next(x for x in api(path,{},'POST') if x.get(field)==value)
ids={}
try:
    for route in ['/','/login','/register','/inicio','/tutorial','/manual','/proyecto?id_proyecto=224','/tarea']:
        check('Pagina '+route,request(route)[0]==200)
    user={'nombre':tag,'correo_electronico':tag+'@example.test','contrasena':'SoloPruebas2026!','rol':'Estudiante','imagen_usuario':'#123456'}
    check('Registro mediante cliente',request('/saveUsuario',user,form=True)[0]==200)
    user=find('/buscarUsuarios','correo_electronico',user['correo_electronico']);ids['usuario']=user
    check('Login valido',request('/verificarLogin',{'correo_electronico':user['correo_electronico'],'contrasena':'SoloPruebas2026!'})[1].get('id_usuario')==user['id_usuario'])
    check('Login invalido',request('/verificarLogin',{'correo_electronico':user['correo_electronico'],'contrasena':'incorrecta'})[1].get('nombre')=='000')
    project={'nombre':tag,'descripcion':'Prueba funcional','fecha_inicio':'2026-11-19','fecha_finalizacion':'2026-11-25','estado_proyecto':'En proceso','fondo':'/Images/blanco.png'}
    check('Crear proyecto desde cliente',request('/saveProyecto',project,form=True)[0]==200)
    project=find('/buscarProyectos','nombre',tag);ids['proyecto']=project
    project['descripcion']='Actualizado';request('/saveProyecto',project,form=True)
    check('Editar proyecto',request('/actualizarProyecto',{'id_proyecto':project['id_proyecto']})[1]['descripcion']=='Actualizado')
    tasks=[]
    for lista in ['pendientes','encurso','terminado']:
        task={'nombre':tag+'_'+lista,'lista':lista,'id_proyecto':project['id_proyecto']}
        check('Crear tarea '+lista,request('/verificarTarea',task)[1]==1)
        task=find('/buscarTareas','nombre',task['nombre']);tasks.append(task)
    ids['tareas']=tasks
    task=tasks[0];task.update(descripcion='Descripcion editada',estado='warning',fecha_vencimiento='2026-11-25',lista='encurso')
    check('Guardar tarea desde formulario',request('/saveTarea',task,form=True)[0]==200)
    loaded=request('/actualizarTarea',{'id_tarea':task['id_tarea']})[1]
    check('Persistir descripcion, fecha, etiqueta y lista',all(loaded[k]==task[k] for k in ['descripcion','estado','fecha_vencimiento','lista']))
    own=request('/obtenerTareas',{'id_proyecto':project['id_proyecto']})[1]
    check('Filtrar tareas por proyecto',len(own)==3 and all(x['id_proyecto']==project['id_proyecto'] for x in own))
    comment={'id_tarea':task['id_tarea'],'id_usuario':tag,'texto_comentario':tag+' comentario','fecha_hora':'2026-11-19 10:00:00'}
    check('Guardar comentario desde cliente',request('/saveComentario',comment)[0]==200)
    comment=find('/buscarComentarios','texto_comentario',comment['texto_comentario']);ids['comentario']=comment
    check('Consultar comentarios de tarea',any(x['id_comentario']==comment['id_comentario'] for x in request('/obtenerComentarios',{'id_tarea':task['id_tarea']})[1]))
    assignment={'id_tarea':task['id_tarea'],'id_usuario':user['id_usuario'],'fecha_asignacion':'2026-11-19'}
    api('/addAsignacion',assignment)
    assignment=next(x for x in api('/buscarAsignaciones',{}) if x.get('id_tarea')==task['id_tarea'] and x.get('id_usuario')==user['id_usuario']);ids['asignacion']=assignment
    assignment['fecha_asignacion']='2026-11-20';api('/updateAsignacion',assignment)
    check('API crear, consultar y editar asignacion',api('/buscarAsignacion?id='+str(assignment['id_asignacion']))['fecha_asignacion']=='2026-11-20')
    comment['texto_comentario']+=' editado';api('/updateComentario',comment)
    check('API editar comentario',api('/buscarComentario?id='+str(comment['id_comentario']))['texto_comentario']==comment['texto_comentario'])
    user['nombre']+=' editado';api('/updateUsuario',user)
    check('API editar usuario',api('/buscarUsuario?id='+str(user['id_usuario']))['nombre']==user['nombre'])
    page=request('/inicio')[1]
    backgrounds=set(re.findall(r"guardarRutaImagen\('([^']+)'\)",page))
    check('Catalogo de fondos disponible',bool(backgrounds))
    for background in sorted(backgrounds):
        check('Fondo '+background,request(background,method='HEAD')[0]==200)
    for asset in ['/Images/manual.mp4','/Images/tutorial.mp4']:
        check('Video '+asset,request(asset,method='HEAD')[0]==200)
    check('Rechazar comentario vacio',request('/saveComentario',{'id_tarea':task['id_tarea'],'texto_comentario':'   '})[0]==400)
    check('Borrar tarea con dependencias',request('/eliminarTarea',{'id_tarea':tasks[0]['id_tarea']})[0]==200)
    check('Eliminar comentarios de tarea borrada',api('/buscarComentario?id='+str(comment['id_comentario'])).get('id_comentario') is None)
    check('Eliminar asignaciones de tarea borrada',api('/buscarAsignacion?id='+str(assignment['id_asignacion'])).get('id_asignacion') is None)
    dependent={'id_tarea':tasks[1]['id_tarea'],'id_usuario':tag,'texto_comentario':tag+' dependiente','fecha_hora':'2026-11-19 10:00:00'}
    api('/addComentario',dependent)
    dependent=find('/buscarComentarios','texto_comentario',dependent['texto_comentario'])
    check('Borrar proyecto con tareas',request('/eliminarProyecto',{'id_proyecto':project['id_proyecto']})[0]==200)
    check('Eliminar tareas de proyecto borrado',len(api('/getTarea',{'id_proyecto':project['id_proyecto']}))==0)
    check('Eliminar comentarios al borrar proyecto',api('/buscarComentario?id='+str(dependent['id_comentario'])).get('id_comentario') is None)
finally:
    for key,endpoint,idfield in [('asignacion','Asignacion','id_asignacion'),('comentario','Comentario','id_comentario')]:
        if key in ids:
            obj=ids[key];api('/delete'+endpoint,obj,'DELETE');check('API eliminar '+key,api('/buscar'+endpoint+'?id='+str(obj[idfield])).get(idfield) is None)
    for task in ids.get('tareas',[]):
        check('Eliminar tarea desde cliente',request('/eliminarTarea',{'id_tarea':task['id_tarea']})[0]==200)
        check('Tarea eliminada en BD',api('/buscarTarea?id_tarea='+str(task['id_tarea'])).get('id_tarea') is None)
    if 'proyecto' in ids:
        obj=ids['proyecto'];check('Eliminar proyecto desde cliente',request('/eliminarProyecto',{'id_proyecto':obj['id_proyecto']})[0]==200)
        check('Proyecto eliminado en BD',api('/buscarProyecto?id_proyecto='+str(obj['id_proyecto'])).get('id_proyecto') is None)
    if 'usuario' in ids:
        obj=ids['usuario'];api('/deleteUsuario',obj,'DELETE');check('API eliminar usuario de prueba',api('/buscarUsuario?id='+str(obj['id_usuario'])).get('id_usuario') is None)
    (ROOT/'resultado-funcional.json').write_text(json.dumps({'prefijo':tag,'pruebas':results},ensure_ascii=False,indent=2),encoding='utf-8')


if any(x['resultado']=='FALLO' for x in results): sys.exit(1)



