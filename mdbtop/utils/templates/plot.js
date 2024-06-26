function render(ctx, event_list=[]) {
    const sys_cpu = []; // percentage usage
    const sys_mem_percent = [] // percentage usage

    const datasets = [];
    const m5lookup = {};

    for (let next of event_list) {
        const ts = next['ts'];
        sys_cpu.push({x: ts, y: next['system']['cpu']['percent']});
        sys_mem_percent.push({x: ts, y: next['system']['memory']['percent']});
        for (let p of next['processes']) {
            // filter mserver5 only
            // event may have captured more than one mserver5
            if (/mserver5/.test(p['pname'])) {
                const pid = p['pid'];
                const wal = p['wal'] || {};
                const bat = p['bat'] || {};
                if (m5lookup.hasOwnProperty(pid)) {
                    const slot = m5lookup[pid];
                    slot.wal.push({x: ts, y: wal['bytes']});
                    slot.wal_files.push({ts, files: (wal['files'] || [])});
                    slot.bat.push({x: ts, y: bat['bytes']});
                    slot.m5_vms.push({x: ts, y: p['vms']});
                    slot.m5_rss.push({x: ts, y: p['rss']});
                    slot.m5_cpu.push({x: ts, y: p['cpu_percent']});
                    slot.m5_mem.push({x: ts, y: p['memory_percent']})
                } else {
                    const slot = {
                        database: p['database'],
                        wal: [{x: ts, y: wal['bytes']}],
                        wal_files: [{ts, files: (wal['files'] || [])}],
                        bat: [{x: ts, y: bat['bytes']}],
                        m5_vms: [{x: ts, y: p['vms']}],
                        m5_rss: [{x: ts, y: p['rss']}],
                        m5_cpu: [{x:ts, y: p['cpu_percent']}],
                        m5_mem: [{x: ts, y: p['memory_percent']}]
                    };
                    m5lookup[pid] = slot;
                }
            }
        }
    }
    // push system datasets
    datasets.push(
        {
            label: 'sys_cpu%',
            data: sys_cpu,
            yAxisID: 'yr'
        }, 
        {
            label: 'sys_mem%',
            data: sys_mem_percent,
            yAxisID: 'yr'
        });

    // push mserver5 datasets
    for (let pid in m5lookup) {
        const m5 = m5lookup[pid];
        datasets.push(
            {
                label: 'm5_cpu%',
                data: m5.m5_cpu,
                yAxisID: 'yr'
            },
            {
                label: 'm5_mem%',
                data: m5.m5_mem,
                yAxisID: 'yr'
            },
            {
                label: 'm5_vms',
                data: m5.m5_vms,
                yAxisID: 'yl'
            },
            {
                label: 'm5_rss',
                data: m5.m5_rss,
                yAxisID: 'yl'
            },
            {
                label: `wal_${m5.database}`,
                data: m5.wal,
                yAxisID: 'yl',
            },
            {
                label: `bat_${m5.database}`,
                data: m5.bat,
                yAxisID: 'yl'
            }
        )
        const lookup = {};
        console.log(m5.wal_files.length)
        for (let d of m5.wal_files) {
            const ts = d.ts;
            const files = d.files;
            for (let file of files) {
                const fname = file['fname'];
                const fsize = file['fsize'];
                if (lookup.hasOwnProperty(fname)) {
                    lookup[fname]['data'].push({x: ts, y: fsize})
                } else {
                    lookup[fname] = {label: fname, data: [{x: ts, y: fsize}], yAxisID: 'yl', type: 'bar', stack: 'bar'}
                }
            }
        }
        // add bar datasets
        for (let k in lookup) {
            datasets.push(lookup[k])
        }
        
    }

    const data = {
        datasets
    }

    const config = {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            stacked: false,
            animation: false,
            scales: {
                x: {
                    type: 'time',
                    // time: {unit: "second"},
                    title: {display: true, text: "Time"},
                    stacked: true
                },
                yl: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {display: true, text: "Size"},
                },
                yr: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {display: true, text: "%"}
                },
            }
        },
    }; 

    const chart = new window.Chart(ctx, config);
    return chart;
}
