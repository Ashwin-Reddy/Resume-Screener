const ExplanationCard = ({ explanation }) => {
  return (
    <div className="bg-box-primary rounded-[32px] p-8 h-full overflow-y-auto">
      <p className="text-white text-[18px] font-inter leading-relaxed">
        {explanation || ""}
      </p>
    </div>
  );
};

export default ExplanationCard;