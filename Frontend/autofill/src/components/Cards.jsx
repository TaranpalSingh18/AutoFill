const Card = (props) => {
  return (
    <div className="bg-black w-50 text-white mt-10 rounded-lg overflow-hidden">
      
      {/* Image */}
      <div>
        <img 
          src={props.image_url} 
          alt="" 
          className="w-full h-40 object-cover"
        />
      </div>

      {/* Details */}
      <div className="p-3">
        <p className="text-sm font-semibold">{props.name}</p>
        <p className="text-xs text-zinc-300">Race: {props.race}</p>
        <p className="text-xs text-zinc-300">Age: {props.age}</p>
      </div>

    </div>
  );
};

export default Card;