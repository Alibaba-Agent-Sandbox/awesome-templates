# Canonical source for both QM SDK invocation adapters.
def invoke(operation,data,timeout):
    if not LOCK.acquire(blocking=False):raise RuntimeError('another original QM operation is active')
    try:
        binary,worker=runtime()
        raw=json.dumps(data,ensure_ascii=False).encode()
        if len(raw)>262144:raise ValueError('native request exceeds256KiB')
        with tempfile.TemporaryDirectory(prefix='abx-qm-home-')as value:
            private=Path(value);private.chmod(0o700)
            descriptor=os.memfd_create('qm-native-request',os.MFD_CLOEXEC)
            with os.fdopen(descriptor,'w+b')as source:
                source.write(raw);source.seek(0)
                code,out,err=PROCESS.run([binary,worker,operation],cwd=private,env=environment(private),timeout=timeout,input_file=source)
        try:value=json.loads(out)
        except ValueError:raise RuntimeError('original QM native result protocol invalid; raw output omitted')from None
        if code:
            if not isinstance(value,dict):value={}
            kind=value.get('error_type')
            if not isinstance(kind,str)or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,63}',kind):kind='NativeFailure'
            detail=''
            stage=value.get('native_stage')
            if stage in ['request','metadata','sdk_import','qm_tools_import','qm_harness_import','qm_workspace_import','qm_acl_import','qm_provider_import','identity','sdk_provision','sdk_roundtrip','provider_configuration','harness_setup','harness_run']:
                detail+='; stage='+stage
            native_code=value.get('error_code')
            if isinstance(native_code,str)and re.fullmatch(r'[A-Z][A-Z0-9_]{0,79}',native_code):detail+='; native_code='+native_code
            missing=value.get('missing_module')
            if isinstance(missing,str)and re.fullmatch(r'[@A-Za-z0-9_./-]{1,128}',missing):detail+='; missing_module='+missing
            counts=value.get('native_counters')
            if isinstance(counts,dict):
                for name in ['model_requests','native_tool_calls','native_tool_results','sdk_shell','sdk_upload','sdk_download']:
                    number=counts.get(name)
                    if type(number)is int and 0<=number<=1000000:detail+='; '+name+'='+str(number)
            raise RuntimeError(redact('original QM native operation failed ('+kind+')'+detail+'; raw diagnostics omitted'))
        if not isinstance(value,dict):raise RuntimeError('original QM result must be an object')
        return redact(value)
    finally:LOCK.release()
