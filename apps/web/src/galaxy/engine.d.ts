export interface Galaxy{burst(x?:number,y?:number,i?:number):void;wordmarkBurst(r:DOMRect|null):void;addEvent(e:{id:string,type:string}):void;setMode(m:string):void;setRotate(v:boolean):void;}
export function createGalaxy(c:HTMLCanvasElement):Galaxy;
