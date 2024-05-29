import { app } from "../../scripts/app.js"

class Visualizer {
    constructor(node, container, visualSrc) {
        this.node = node

        this.iframe = document.createElement('iframe')
        Object.assign(this.iframe, {
            scrolling: "scroll",
            overflow: "hidden"
        })
        this.iframe.src = "/extensions/ComfyUI-mobvoi-openapi/html/" + visualSrc + ".html"
        this.container=container;
        container.appendChild(this.iframe)
    }

    updateVisual(params) {
        var that=this;
        const iframeDocument = this.iframe.contentWindow.document
        const container = iframeDocument.getElementById('container')

        if(container){
            if(params&&params.html)
                container.innerHTML=params.html;
            else if(params&&params.indexOf('http')>=0){
                container.innerHTML='<video src="'+params+'" />';
            }else{
                container.innerHTML='<div style="width:600px;height:500px;"></div>';
            }
            
            var video = iframeDocument.querySelector("video");

            if(video){
                video.addEventListener("loadedmetadata", (event) => {
                    //that.iframe.style.width=event.target.videoWidth+'px';
                    //that.iframe.style.height=event.target.videoHeight+'px';
                    //that.container.style.width=event.target.videoWidth+'px';
                    //that.container.style.height=event.target.videoHeight+'px';
                });
            }
        }
    }

    remove() {
        this.container.remove()
    }
}

function createVisualizer(node, inputName, typeName, inputData, app) {
    node.name = inputName

    const widget = {
        type: typeName,
        name: "previewhtml",
        callback: () => {},
        draw : function(ctx, node, widgetWidth, widgetY, widgetHeight) {
            const margin = 10
            const top_offset = 5
            const visible = app.canvas.ds.scale > 0.5 && this.type === typeName
            const w = widgetWidth - margin * 4
            const clientRectBound = ctx.canvas.getBoundingClientRect()
            const transform = new DOMMatrix()
                .scaleSelf(
                    clientRectBound.width / ctx.canvas.width,
                    clientRectBound.height / ctx.canvas.height
                )
                .multiplySelf(ctx.getTransform())
                .translateSelf(margin, margin + widgetY)
            
            Object.assign(this.visualizer.style, {
                left: `${transform.a * margin + transform.e}px`,
                top: `${transform.d + transform.f + top_offset}px`,
                width: `${(w * transform.a)}px`,
                height: `${(w * transform.d - widgetHeight - (margin * 15) * transform.d)}px`,
                position: "absolute",
                overflow: "hidden",
                zIndex: app.graph._nodes.indexOf(node),
            })

            Object.assign(this.visualizer.children[0].style, {
                transformOrigin: "50% 50%",
                width: '100%',
                height: '100%',
                border: '0 none',
            })

            this.visualizer.hidden = !visible
        },
    }

    const container = document.createElement('div')
    container.id = `ComfyHtml_${inputName}`

    node.visualizer = new Visualizer(node, container, typeName)
    widget.visualizer = container
    widget.parent = node

    document.body.appendChild(widget.visualizer)

    node.addCustomWidget(widget)

    node.updateParameters = (params) => {
        console.log(params)
        node.visualizer.updateVisual(params)
    }

    node.updateParameters(node.widgets[0].value);

    // Events for drawing backgound
    node.onDrawBackground = function (ctx) {
        if (!this.flags.collapsed) {
            node.visualizer.iframe.hidden = false
        } else {
            node.visualizer.iframe.hidden = true
        }
    }

    // Make sure visualization iframe is always inside the node when resize the node
    node.onResize = function () {
        let [w, h] = this.size
        if (w <= 600) w = 600
        if (h <= 500) h = 500

        if (w > 600) {
            //h = w - 100
        }

        this.size = [w, h]
    }

    // Events for remove nodes
    node.onRemoved = () => {
        for (let w in node.widgets) {
            if (node.widgets[w].visualizer) {
                node.widgets[w].visualizer.remove()
            }
        }
    }


    return {
        widget: widget,
    }
}

function registerVisualizer(nodeType, nodeData, nodeClassName, typeName){
    if (nodeData.name == nodeClassName) {
        console.log("[Html Visualizer] Registering node: " + nodeData.name)

        const onNodeCreated = nodeType.prototype.onNodeCreated

        nodeType.prototype.onNodeCreated = async function() {
            const r = onNodeCreated
                ? onNodeCreated.apply(this, arguments)
                : undefined

            let PreviewhtmlNode = app.graph._nodes.filter(
                (wi) => wi.type == nodeClassName
            )
            let nodeName = `PreviewhtmlNode_${PreviewhtmlNode.length}`

            console.log(`[ComfyHtml] Create: ${nodeName}`)

            const result = await createVisualizer.apply(this, [this, nodeName, typeName, {}, app])

            this.setSize([600, 500])

            return r
        }

        nodeType.prototype.onExecuted = async function(message) {
            if (message?.html) {
                this.updateParameters(message.html[0])
            }
        }
    }
}

app.registerExtension({
    name: "Html.Viewer",

    async init (app) {

    },

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        registerVisualizer(nodeType, nodeData, "HtmlViewer", "htmlVisualizer")
    },
})