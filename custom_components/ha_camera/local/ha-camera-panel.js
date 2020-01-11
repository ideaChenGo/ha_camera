class HaCameraPanel extends HTMLElement {
    constructor() {
        super()
        const shadow = this.attachShadow({ mode: 'open' });
        const div = document.createElement('ha-card');
        div.className = 'ha-camera-panel'
        div.innerHTML = `
        <div class="card-header">
            <a class="name">
                摄像头
            </a>
        </div>
        
        <div class="card-content">
          <img id="snapshot" />
		  <canvas id="video-canvas" class="hide"></canvas>
        </div>		
        <style>
			#snapshot,
			#video-canvas{width:100%;}		
			.hide{display:none;}
			.fullscreen{
				position: absolute;
				width: 98%;
				top: 10px;
				left: 1%;
			}
        </style>
        `
        shadow.appendChild(div)
        this.shadow = shadow
        this.$ = this.shadow.querySelector.bind(this.shadow)


    }

    toast(message) {
        document.querySelector('home-assistant').dispatchEvent(new CustomEvent("hass-notification", { detail: { message } }))
    }
	
	loadScript(url){
		return new Promise((resolve)=>{
			let { $ } = this
			let id = url.replace(/[^0-9a-zA-Z]/g,'')
			let script = $(`#${id}`)
			if(script){
				resolve()
			}else{
				script = document.createElement('script')
				script.id = id
				script.src = url
				script.onload = ()=>{
					resolve()
				}
				this.shadow.appendChild(script)
			}			
		})
	}

    get hass() {
        return this._hass
	}
	
	get r(){
		let d = new Date()
		return `${d.getFullYear()}${d.getMonth()}${d.getDate()}${d.getHours()}${d.getMinutes()}`
	}

    set hass(hass) {
        // console.log(hass)
        this._hass = hass
        let { states } = hass
		let state = states['weblink.she_xiang_tou']
		if(state){
			let { $, config } = this
			let { snapshot, ws } = config
			if(snapshot){
				const canvas = $('#video-canvas');
				const ss = $('#snapshot')
				ss.src = `${state.state}?r=${this.r}&url=${snapshot}`
				ss.onclick = ()=>{
					ss.classList.toggle('hide')
					canvas.classList.toggle('hide')
					$('.ha-camera-panel').classList.toggle('fullscreen')
					
					if(ws){
						if(!window.haCameraPlayer){
							window.haCameraPlayer = new JSMpeg.Player(ws, { canvas });
						}else{
							let cv = window.haCameraPlayer.options.canvas
							// console.log(canvas, cv)
							$('.card-content').replaceChild(cv, canvas)
						}
					}else{
						this.toast('没有配置ws链接')
					}			
				}
				$('.card-header .name').onclick = ()=>{
					ss.onclick()
				}
				this.loadScript(`${state.state}/1.0/jsmpeg.min.js`).then(()=>{
				})
			}
					
		}
    }

    setConfig(config) {
        this.config = config || {};
    }

    getCardSize() {
        return 3
    }
}

customElements.define('ha-camera-panel', HaCameraPanel);